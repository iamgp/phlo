from dagster import ConfigurableResource
from dagster_dbt import DbtCliResource

class DbtProfiles(ConfigurableResource):
    project_dir: str = "/dbt"
    profiles_dir: str = "/dbt/profiles"
    target_duckdb: str = "duckdb"
    target_postgres: str = "postgres"

    def cli(self) -> DbtCliResource:
        # duckdb first, then postgres marts
        return DbtCliResource(project_dir=self.project_dir, profiles_dir=self.profiles_dir)
