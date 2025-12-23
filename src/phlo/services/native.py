"""
Native Process Manager

Manages native (subprocess) execution of services without Docker.
Used for running phlo-api and Observatory natively.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from re import Match

import httpx

from phlo.services.discovery import ServiceDefinition

logger = logging.getLogger(__name__)


@dataclass
class NativeProcess:
    """Represents a running native process."""

    name: str
    process: subprocess.Popen[str]
    health_check_url: str | None = None
    started_at: float = field(default_factory=time.time)

    @property
    def is_running(self) -> bool:
        """Check if process is still running."""
        return self.process.poll() is None

    @property
    def pid(self) -> int:
        """Get process ID."""
        return self.process.pid


class NativeProcessManager:
    """Manages native processes for services in dev mode (no Docker)."""

    def __init__(self, project_root: Path, log_dir: Path | None = None):
        self.project_root = project_root
        self.log_dir = log_dir
        self._processes: dict[str, NativeProcess] = {}

    def can_run_dev(self, service: ServiceDefinition) -> bool:
        """Check if a service can run in dev mode as a subprocess."""
        return bool(service.dev and service.dev.get("command"))

    def _expand_env_vars(self, value: str, env: dict[str, str]) -> str:
        pattern = re.compile(r"\$\{([A-Z0-9_]+)(?::-([^}]*))?\}")

        def repl(match: Match[str]) -> str:
            var = match.group(1)
            default = match.group(2)
            if var in env:
                return env[var]
            if default is not None:
                return default
            raise KeyError(var)

        return pattern.sub(repl, value)

    async def start_service(
        self,
        service: ServiceDefinition,
        env_overrides: dict[str, str] | None = None,
    ) -> NativeProcess | None:
        """Start a service as a subprocess in dev mode.

        Args:
            service: Service definition with dev config.
            env_overrides: Additional environment variables.

        Returns:
            NativeProcess if started, None if not supported.
        """
        if not self.can_run_dev(service):
            logger.warning(f"Service {service.name} does not support dev mode subprocess")
            return None

        dev_config = service.dev
        command = dev_config.get("command", [])

        if not command:
            logger.error(f"Service {service.name} has no dev command")
            return None

        # Build environment
        env = os.environ.copy()
        if dev_env := dev_config.get("environment"):
            for key, value in dev_env.items():
                if isinstance(value, str):
                    env[key] = self._expand_env_vars(value, env)
                else:
                    env[key] = str(value)
        if env_overrides:
            for key, value in env_overrides.items():
                env[key] = self._expand_env_vars(value, env)

        expanded_command: list[str] = []
        for arg in command:
            if isinstance(arg, str):
                expanded_command.append(self._expand_env_vars(arg, env))
        command = expanded_command

        # Resolve working directory
        cwd_template = dev_config.get("cwd", ".")
        cwd = self._resolve_path(cwd_template, service)

        # Handle build step if required
        if dev_config.get("requires_build"):
            should_build = True
            build_if_missing = dev_config.get("build_if_missing")
            if isinstance(build_if_missing, str):
                build_target = (cwd / build_if_missing).resolve()
                if build_target.exists():
                    should_build = False
            build_cmd = dev_config.get("build_command", [])
            if build_cmd and should_build:
                logger.info(f"Building {service.name}...")
                try:
                    build_result = subprocess.run(
                        build_cmd,
                        cwd=cwd,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5 minute timeout for builds
                    )
                    if build_result.returncode != 0:
                        logger.error(f"Build failed for {service.name}: {build_result.stderr}")
                        return None
                except subprocess.TimeoutExpired:
                    logger.error(f"Build timed out for {service.name}")
                    return None

        # Start the process
        logger.info(f"Starting {service.name} in dev mode: {' '.join(command)}")
        log_file = None
        try:
            stdout = None
            if self.log_dir is not None:
                self.log_dir.mkdir(parents=True, exist_ok=True)
                log_path = self.log_dir / f"{service.name}.log"
                log_file = open(log_path, "a", encoding="utf-8")
                stdout = log_file
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=stdout,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
        except Exception as e:
            logger.error(f"Failed to start {service.name}: {e}")
            return None
        finally:
            if log_file is not None:
                log_file.close()

        health_check_url = dev_config.get("health_check")
        if isinstance(health_check_url, str):
            health_check_url = self._expand_env_vars(health_check_url, env)
        native_process = NativeProcess(
            name=service.name,
            process=process,
            health_check_url=health_check_url,
        )
        self._processes[service.name] = native_process

        # Wait for health check if configured
        if health_check_url:
            healthy = await self._wait_for_health(health_check_url, timeout=30)
            if not healthy:
                logger.warning(f"Service {service.name} started but health check failed")

        return native_process

    async def stop_service(self, name: str, timeout: int = 10) -> bool:
        """Stop a native service.

        Args:
            name: Service name.
            timeout: Seconds to wait for graceful shutdown.

        Returns:
            True if stopped, False if not found or failed.
        """
        native_process = self._processes.get(name)
        if not native_process:
            return False

        process = native_process.process
        if not native_process.is_running:
            del self._processes[name]
            return True

        # Try graceful shutdown first
        logger.info(f"Stopping {name} (pid {process.pid})...")
        try:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                logger.warning(f"Service {name} did not stop gracefully, killing...")
                process.kill()
                process.wait(timeout=5)
        except Exception as e:
            logger.error(f"Error stopping {name}: {e}")
            return False

        del self._processes[name]
        return True

    async def stop_all(self, timeout: int = 10) -> None:
        """Stop all running native services."""
        for name in list(self._processes.keys()):
            await self.stop_service(name, timeout)

    def get_running_services(self) -> list[str]:
        """Get list of running service names."""
        return [name for name, proc in self._processes.items() if proc.is_running]

    def get_process(self, name: str) -> NativeProcess | None:
        """Get a native process by name."""
        return self._processes.get(name)

    def _resolve_path(self, template: str, service: ServiceDefinition) -> Path:
        """Resolve path template."""
        resolved = template
        if "{project_root}" in resolved:
            resolved = resolved.replace("{project_root}", str(self.project_root))
        if "{source_path}" in resolved and service.source_path:
            resolved = resolved.replace("{source_path}", str(service.source_path))
        return Path(resolved)

    async def _wait_for_health(self, url: str, timeout: int = 30) -> bool:
        """Wait for health check to pass."""
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            while time.time() - start < timeout:
                try:
                    response = await client.get(url)
                    if response.status_code < 500:
                        return True
                except Exception:
                    pass
                await asyncio.sleep(1)
        return False
