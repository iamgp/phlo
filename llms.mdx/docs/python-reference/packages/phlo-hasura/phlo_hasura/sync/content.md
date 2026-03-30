# sync (/docs/python-reference/packages/phlo-hasura/phlo_hasura/sync)



Hasura metadata export, import and schema management.

This module provides classes and functions for managing Hasura metadata
lifecycle operations including export, import, diff calculation, and
version control integration.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;HasuraMetadataSync&#x22;" href="&#x22;/docs/python-reference/packages/phlo-hasura/phlo_hasura/sync/HasuraMetadataSync&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;export_metadata&#x22;" type="&#x22;(output_path=None, verbose=True) -> str&#x22;">
      Convenience function to export metadata.

      Simple wrapper around HasuraMetadataSync.export\_metadata() for
      quick metadata exports without instantiating the class.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > export\_metadata("backup.json")
        > > > 'backup.json'
        > > > json\_str = export\_metadata()
        > > > print(json\_str\[:50])
        > > > \{"version": 3, "sources": \[...]}
      </Callout>

      <PySourceCode>
        ```python
        def export_metadata(output_path: Optional[str] = None, verbose: bool = True) -> str:
            """Convenience function to export metadata.

            Simple wrapper around HasuraMetadataSync.export_metadata() for
            quick metadata exports without instantiating the class.

            Args:
                output_path: Path to save metadata JSON file. If None, returns
                    metadata as a JSON string.
                verbose: Print progress messages.

            Returns:
                Path where metadata was saved (if output_path provided) or
                JSON string of the metadata.

            Example:
                >>> export_metadata("backup.json")
                'backup.json'
                >>> json_str = export_metadata()
                >>> print(json_str[:50])
                {"version": 3, "sources": [...]}

            """
            if verbose:
                logger.info("Exporting Hasura metadata...")

            syncer = HasuraMetadataSync()
            metadata = syncer.export_metadata(output_path)

            if output_path:
                if verbose:
                    logger.info("✓ Metadata exported to %s", output_path)
                return output_path
            else:
                if verbose:
                    logger.info("✓ Metadata exported")
                return json.dumps(metadata, indent=2)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;output_path&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Path to save metadata JSON file. If None, returns
          metadata as a JSON string.
        </PyParameter>

        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Print progress messages.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Path where metadata was saved (if output\_path provided) or
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;apply_metadata&#x22;" type="&#x22;(input_path, verbose=True) -> None&#x22;">
      Convenience function to apply metadata.

      Simple wrapper around HasuraMetadataSync.import\_metadata() for
      quick metadata imports without instantiating the class.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > apply\_metadata("backup.json")
        > > > apply\_metadata("production-metadata.json", verbose=False)
      </Callout>

      <PySourceCode>
        ```python
        def apply_metadata(input_path: str, verbose: bool = True) -> None:
            """Convenience function to apply metadata.

            Simple wrapper around HasuraMetadataSync.import_metadata() for
            quick metadata imports without instantiating the class.

            Args:
                input_path: Path to the metadata JSON file to import.
                verbose: Print progress messages.

            Raises:
                FileNotFoundError: If the input file does not exist.
                requests.RequestException: If the API call fails.

            Example:
                >>> apply_metadata("backup.json")
                >>> apply_metadata("production-metadata.json", verbose=False)

            """
            if verbose:
                logger.info("Applying metadata from %s...", input_path)

            syncer = HasuraMetadataSync()
            syncer.import_metadata(input_path)

            if verbose:
                logger.info("✓ Metadata applied")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;input_path&#x22;" type="&#x22;str&#x22;" value="undefined">
          Path to the metadata JSON file to import.
        </PyParameter>

        <PyParameter name="&#x22;verbose&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Print progress messages.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
