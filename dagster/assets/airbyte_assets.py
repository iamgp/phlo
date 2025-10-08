from dagster import AssetExecutionContext
from dagster_airbyte import AirbyteResource, load_assets_from_airbyte_instance

def build_airbyte_assets(airbyte_instance: AirbyteResource):
    """
    Load all Airbyte connections as Dagster assets.
    Each Airbyte connection sync becomes a materialized asset.
    """
    return load_assets_from_airbyte_instance(airbyte_instance)
