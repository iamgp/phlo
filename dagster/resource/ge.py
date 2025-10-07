from dagster import ConfigurableResource
import subprocess

class GreatExpectationsCLI(ConfigurableResource):
    ge_dir: str = "/great_expectations"

    def run_checkpoint(self, name: str):
        subprocess.run(
            ["great_expectations", "checkpoint", "run", name],
            cwd=self.ge_dir,
            check=True,
        )
