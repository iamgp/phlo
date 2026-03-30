# RawDataOutput (/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/asset_outputs/RawDataOutput)



Output model for raw data ingestion assets.

Captures the status and metadata of raw data ingestion operations,
including file counts and paths.

Attributes [#attributes]

<PyAttribute name="&#x22;status&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(..., description=\&#x22;Status of the raw data: 'available' or 'no_data'\&#x22;)&#x22;">
  Status of the raw data ingestion - "available" if data was
  successfully ingested, "no\_data" if no data was found.
</PyAttribute>

<PyAttribute name="&#x22;path&#x22;" type="&#x22;str&#x22;" value="&#x22;Field(..., description='Path to the raw data directory')&#x22;">
  Path to the raw data directory (local or S3/MinIO path).
</PyAttribute>

<PyAttribute name="&#x22;file_count&#x22;" type="&#x22;int&#x22;" value="&#x22;Field(default=0, ge=0, description='Total number of parquet files found')&#x22;">
  Total number of parquet files found. Default 0.
</PyAttribute>

<PyAttribute name="&#x22;files&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;Field(default_factory=list, description='List of file names (up to 10 for display)', max_length=10)&#x22;">
  List of file names (up to 10 for display purposes).
</PyAttribute>
