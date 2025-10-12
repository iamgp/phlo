"""
Lakehouse Kit - Data Lakehouse Platform

Error Handling Conventions
===========================

This codebase follows consistent error handling patterns:

1. Validation Errors
   - Use: ValueError with clear, actionable message
   - When: Input validation fails, configuration is invalid
   - Action: Always log context before raising

2. External Service Failures (transient)
   - Use: Log warning/error and return None or default value
   - When: API calls fail, network issues, temporary service unavailability
   - Action: Use retry logic (tenacity) for resilient operations
   - Examples: Airbyte API calls, external data sources

3. Critical Failures (cannot proceed)
   - Use: RuntimeError or specific exception type
   - When: Required resource unavailable, fatal configuration error
   - Action: Always log context before raising

4. General Exception Handling
   - Always log exceptions with context using logger.exception()
   - Avoid bare except: clauses
   - Catch specific exceptions when possible
   - Include relevant identifiers (connection names, file paths, etc.) in log messages

Example:
    def _resolve_connection_id(config: AirbyteConnectionConfig) -> str:
        connection_id = _lookup_connection_by_name(config.connection_name)

        if connection_id:
            return connection_id

        if config.connection_id:
            logger.info(f"Using fallback ID for '{config.connection_name}'")
            return config.connection_id

        # Critical - can't proceed without connection ID
        raise ValueError(
            f"Cannot resolve Airbyte connection '{config.connection_name}'. "
            "Connection not found in workspace and no fallback ID provided."
        )
"""
