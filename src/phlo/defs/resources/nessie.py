# nessie.py - Dagster resource for Nessie catalog operations
# Provides branch management for Write-Audit-Publish pattern

from __future__ import annotations

import logging
from typing import Any

import requests
from dagster import ConfigurableResource

from phlo.config import config

logger = logging.getLogger(__name__)


class NessieResource(ConfigurableResource):
    """
    Dagster resource for Nessie catalog branch management.
    
    Supports the Write-Audit-Publish pattern:
    - Create feature branches for isolated work
    - Merge validated data to main
    - List and manage branches
    
    Example:
        ```python
        @asset
        def merge_after_validation(nessie: NessieResource):
            # Merge dev branch to main after quality checks pass
            nessie.merge("dev", "main")
        ```
    """
    
    api_url: str = config.nessie_api_v1_uri
    
    def list_branches(self) -> list[dict[str, Any]]:
        """List all branches in the catalog."""
        response = requests.get(f"{self.api_url}/trees", timeout=10)
        response.raise_for_status()
        return response.json().get("references", [])
    
    def get_branch(self, name: str) -> dict[str, Any]:
        """Get branch details including current hash."""
        response = requests.get(f"{self.api_url}/trees/tree/{name}", timeout=10)
        response.raise_for_status()
        return response.json()
    
    def create_branch(self, name: str, from_branch: str = "main") -> dict[str, Any]:
        """
        Create a new branch from an existing branch.
        
        Args:
            name: Name of the new branch
            from_branch: Source branch to fork from (default: main)
            
        Returns:
            Branch details
        """
        # Get source branch hash
        source = self.get_branch(from_branch)
        source_hash = source.get("hash")
        
        if not source_hash:
            raise ValueError(f"Could not get hash for branch '{from_branch}'")
        
        # Create new branch
        response = requests.post(
            f"{self.api_url}/trees/tree",
            json={"type": "BRANCH", "name": name, "hash": source_hash},
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"Created branch '{name}' from '{from_branch}'")
        return response.json()
    
    def delete_branch(self, name: str) -> None:
        """Delete a branch (cannot delete main)."""
        if name == "main":
            raise ValueError("Cannot delete main branch")
        
        branch = self.get_branch(name)
        branch_hash = branch.get("hash")
        
        response = requests.delete(
            f"{self.api_url}/trees/tree/{name}",
            params={"expectedHash": branch_hash},
            timeout=10,
        )
        response.raise_for_status()
        logger.info(f"Deleted branch '{name}'")
    
    def merge(
        self, 
        from_branch: str, 
        to_branch: str = "main",
        message: str | None = None,
    ) -> dict[str, Any]:
        """
        Merge one branch into another.
        
        This is the key operation for Write-Audit-Publish:
        After quality checks pass on a feature branch, merge to main.
        
        Args:
            from_branch: Source branch with validated data
            to_branch: Target branch (default: main)
            message: Optional merge commit message
            
        Returns:
            Merge result details
        """
        # Get source and target branch info
        source = self.get_branch(from_branch)
        target = self.get_branch(to_branch)
        
        source_hash = source.get("hash")
        target_hash = target.get("hash")
        
        if not source_hash or not target_hash:
            raise ValueError("Could not get branch hashes for merge")
        
        # Perform merge
        merge_message = message or f"Merge {from_branch} into {to_branch}"
        
        response = requests.post(
            f"{self.api_url}/trees/tree/{to_branch}/merge",
            params={"expectedHash": target_hash},
            json={
                "fromRefName": from_branch,
                "fromHash": source_hash,
                "message": merge_message,
            },
            timeout=30,
        )
        response.raise_for_status()
        
        logger.info(f"Merged '{from_branch}' into '{to_branch}'")
        return response.json()
    
    def branch_exists(self, name: str) -> bool:
        """Check if a branch exists."""
        try:
            self.get_branch(name)
            return True
        except requests.HTTPError:
            return False
    
    def ensure_branch(self, name: str, from_branch: str = "main") -> dict[str, Any]:
        """
        Ensure a branch exists, creating it if necessary.
        
        Args:
            name: Branch name
            from_branch: Source branch if creation needed
            
        Returns:
            Branch details
        """
        if self.branch_exists(name):
            return self.get_branch(name)
        return self.create_branch(name, from_branch)
