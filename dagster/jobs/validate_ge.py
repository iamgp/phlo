from dagster import job, op
from ..resources.ge import GreatExpectationsCLI

@op
def ge_precheck(ge: GreatExpectationsCLI):
    ge.run_checkpoint("checkpoint_stg")

@op
def ge_postcheck(ge: GreatExpectationsCLI):
    ge.run_checkpoint("checkpoint_curated")

@job(resource_defs={"ge": GreatExpectationsCLI})
def ge_prepost_validation_job():
    ge_precheck()
    ge_postcheck()
