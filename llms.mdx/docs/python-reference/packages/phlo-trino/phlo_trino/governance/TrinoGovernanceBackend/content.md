# TrinoGovernanceBackend (/docs/python-reference/packages/phlo-trino/phlo_trino/governance/TrinoGovernanceBackend)



GovernanceBackend implementation using Trino SQL grants.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, trino=None) -> None&#x22;">
  Initialize the governance backend with optional Trino resource.

  <PySourceCode>
    ```python
    def __init__(self, trino: TrinoResource | None = None) -> None:
        """Initialize the governance backend with optional Trino resource."""
        self._trino = trino or TrinoResource()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;trino&#x22;" type="&#x22;TrinoResource | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;list_policies&#x22;" type="&#x22;(self, *, table_name=None) -> list[dict[str, Any]]&#x22;">
  List grants, optionally filtered by table.

  <PySourceCode>
    ```python
    def list_policies(self, *, table_name: str | None = None) -> list[dict[str, Any]]:
        """List grants, optionally filtered by table."""
        if table_name is not None:
            _validate_identifier(table_name, "table_name")
        sql = f"SHOW GRANTS ON TABLE {table_name}" if table_name else "SHOW GRANTS"
        try:
            rows = self._trino.execute(sql)
        except Exception:
            logger.warning(
                "trino_governance_list_policies_failed",
                table_name=table_name,
                exc_info=True,
            )
            return []
        # Trino SHOW GRANTS columns:
        # 0=grantor 1=grantor_type 2=grantee 3=grantee_type
        # 4=catalog 5=schema 6=table 7=privilege 8=is_grantable 9=with_hierarchy
        policies: list[dict[str, Any]] = []
        for row in rows:
            policies.append(
                {
                    "grantor": row[0] if len(row) > 0 else None,
                    "grantor_type": row[1] if len(row) > 1 else None,
                    "grantee": row[2] if len(row) > 2 else None,
                    "grantee_type": row[3] if len(row) > 3 else None,
                    "catalog": row[4] if len(row) > 4 else None,
                    "schema": row[5] if len(row) > 5 else None,
                    "table": row[6] if len(row) > 6 else None,
                    "privilege": row[7] if len(row) > 7 else None,
                    "grantable": row[8] if len(row) > 8 else None,
                    "with_hierarchy": row[9] if len(row) > 9 else None,
                }
            )
        return policies
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;apply_policy&#x22;" type="&#x22;(self, *, policy) -> None&#x22;">
  Apply a GRANT or DENY via Trino SQL.

  <PySourceCode>
    ```python
    def apply_policy(self, *, policy: AccessPolicy) -> None:
        """Apply a GRANT or DENY via Trino SQL."""
        action = policy.action.upper()
        if action not in _ALLOWED_ACTIONS:
            raise ValueError(f"Unsupported action: {action!r}")
        _validate_identifier(policy.table_pattern, "table_pattern")
        _validate_identifier(policy.principal, "principal")
        if policy.columns:
            logger.warning("trino_governance_column_grants_unsupported", columns=policy.columns)

        if policy.effect == "DENY":
            sql = f"DENY {action} ON TABLE {policy.table_pattern} TO {policy.principal}"
        else:
            sql = f"GRANT {action} ON TABLE {policy.table_pattern} TO {policy.principal}"

        logger.info(
            "trino_governance_apply_policy",
            sql=sql,
            principal=policy.principal,
            table=policy.table_pattern,
            action=action,
        )
        self._trino.execute(sql)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;policy&#x22;" type="&#x22;AccessPolicy&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;revoke_policy&#x22;" type="&#x22;(self, *, policy_id) -> None&#x22;">
  Revoke a grant. policy\_id format: `ACTION:TABLE:PRINCIPAL`.

  <PySourceCode>
    ```python
    def revoke_policy(self, *, policy_id: str) -> None:
        """Revoke a grant. policy_id format: ``ACTION:TABLE:PRINCIPAL``."""
        parts = policy_id.split(":", 2)
        if len(parts) != 3:
            msg = f"policy_id must be 'ACTION:TABLE:PRINCIPAL', got: {policy_id}"
            raise ValueError(msg)
        action, table, principal = parts
        if action.upper() not in _ALLOWED_ACTIONS:
            raise ValueError(f"Unsupported action: {action!r}")
        _validate_identifier(table, "table")
        _validate_identifier(principal, "principal")
        sql = f"REVOKE {action.upper()} ON TABLE {table} FROM {principal}"
        logger.info("trino_governance_revoke_policy", sql=sql, policy_id=policy_id)
        self._trino.execute(sql)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;policy_id&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;check_access&#x22;" type="&#x22;(self, *, principal, table_name, action) -> bool&#x22;">
  Check if principal has the specified privilege on a table.

  <PySourceCode>
    ```python
    def check_access(self, *, principal: str, table_name: str, action: str) -> bool:
        """Check if principal has the specified privilege on a table."""
        policies = self.list_policies(table_name=table_name)
        action_upper = action.upper()
        for policy in policies:
            if policy.get("grantee") == principal and policy.get("privilege") == action_upper:
                return True
        return False
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;principal&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

    <PyParameter name="&#x22;action&#x22;" type="&#x22;str&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;bool&#x22;" />
</PyFunction>
