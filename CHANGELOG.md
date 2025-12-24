# Changelog

## [0.1.0-alpha.1](https://github.com/iamgp/phlo/compare/v0.1.0-alpha.0...v0.1.0-alpha.1) (2025-12-07)


### ⚠ BREAKING CHANGES

* Remove phlo contracts module in favor of dbt native governance
    - Delete src/phlo/contracts/ directory
    - Delete phlo contract CLI command
    - Delete contracts tests
    - Rely on dbt contracts, freshness, and tests for governance
* Complete removal of DuckLake architecture

### Features

* add --dev mode to phlo services CLI and glucose-platform example ([13aa604](https://github.com/iamgp/phlo/commit/13aa6044163d29b94dd226f82329c643a98c82ff))
* add audit documentation files ([#23](https://github.com/iamgp/phlo/issues/23)) ([572a330](https://github.com/iamgp/phlo/commit/572a33062f35d141fed2e7c35fb11f8c3bb25dce))
* add automatic dbt transform discovery to framework ([e434202](https://github.com/iamgp/phlo/commit/e434202469004a7ad99cb24d0cd56f84901bd5ea))
* add CASCADE_HOST_PLATFORM for macOS Docker executor stability ([fe593cb](https://github.com/iamgp/phlo/commit/fe593cbb053cde6da7fd545caa436cfc71225bb5))
* add configurable merge strategies ([744df8c](https://github.com/iamgp/phlo/commit/744df8c1ca8d85b96fe25a88f9bc95023b6187b8))
* add docker services management and fix materialize command ([9f6d759](https://github.com/iamgp/phlo/commit/9f6d75967fdfd398bfd081deeb285b381047abdc))
* add GitHub data ingestion and improve asset naming ([14d619c](https://github.com/iamgp/phlo/commit/14d619c93a4861ec5e7ec76043ba019a3cf7b020))
* add github-stats phlo example ([1f75381](https://github.com/iamgp/phlo/commit/1f75381aadad996e5dfd95b44b1460b09a7b9005))
* add infrastructure configuration to phlo.yaml ([6e0554c](https://github.com/iamgp/phlo/commit/6e0554c82818a9b09b58444f38fc16ff6a50cfbc))
* add Nessie branching support and auto dbt compile ([a732815](https://github.com/iamgp/phlo/commit/a732815345e245181510fb9a60cf1205b2289142))
* add NessieResource and auto-init branches on startup ([13b619c](https://github.com/iamgp/phlo/commit/13b619c282343fd3f4c2249ba1f215e56fa9104d))
* add OpenMetadata data catalog integration ([#18](https://github.com/iamgp/phlo/issues/18)) ([9102516](https://github.com/iamgp/phlo/commit/91025169bcc314003943f2b3e146c2bcf8d84e1a))
* add Pandera validation for ingestion and fact tables ([#19](https://github.com/iamgp/phlo/issues/19)) ([117f8bb](https://github.com/iamgp/phlo/commit/117f8bb6276a30c8dedeba47e256c1c909497f34))
* add PhloSchema base class and dbt model Pandera generation ([d8bbc0c](https://github.com/iamgp/phlo/commit/d8bbc0c1e1cd749c46045c45e8c90a5e540414bf))
* add proper kind icons for assets in Dagster UI ([83aad98](https://github.com/iamgp/phlo/commit/83aad9816fda7ded2571d5341f3605d920b43fbf))
* add Pydantic validation for asset outputs ([#7](https://github.com/iamgp/phlo/issues/7)) ([768f6a3](https://github.com/iamgp/phlo/commit/768f6a36ac2d8e7137b526bd91bd82dc4a3f22e6))
* add sqruff linting tool ([#24](https://github.com/iamgp/phlo/issues/24)) ([5f594e7](https://github.com/iamgp/phlo/commit/5f594e7eb6f2be2a3ea2e4e3c90248a73609bacc))
* add Trino driver to Superset image ([d23a842](https://github.com/iamgp/phlo/commit/d23a842df3f1c35f20b6ce6367154e84533ffc21))
* added a dedicated image for the hub UI  ([#3](https://github.com/iamgp/phlo/issues/3)) ([2a372e7](https://github.com/iamgp/phlo/commit/2a372e731222348877e24c8b641dd2474ac1aac4))
* airbyte service ([7720cc2](https://github.com/iamgp/phlo/commit/7720cc286c2b839bb815b3b794d52c2ff3696825))
* **api:** implement API layer automation per spec 007 ([40e46e8](https://github.com/iamgp/phlo/commit/40e46e8a704dd0a9f4f00d8a2b0059bec88503e4))
* auto-publish dbt marts to Postgres for BI ([33e7ae8](https://github.com/iamgp/phlo/commit/33e7ae8c7870e6a39486f285434653e6e661c69b))
* blog posts ([3e00288](https://github.com/iamgp/phlo/commit/3e002884c9ff1bf19870544fe8ea0a867b1868d3))
* **catalog:** implement OpenMetadata integration per spec 009 ([f3f0f08](https://github.com/iamgp/phlo/commit/f3f0f08560c1b912f608830a6b8765f0af5ba550))
* centralized configuration management (AUDIT.md tasks 11-13) ([#6](https://github.com/iamgp/phlo/issues/6)) ([41bcd5e](https://github.com/iamgp/phlo/commit/41bcd5edbce9fe2187761814fd747a5b4e1b30a5))
* **cli:** implement CLI commands per spec 002 ([cf761db](https://github.com/iamgp/phlo/commit/cf761db2e5f5af9d5f0e1c9833c42d7911e2884a))
* **cli:** implement schema catalog and data contracts per specs 004 and 010 ([573c230](https://github.com/iamgp/phlo/commit/573c230ba67f769bbec7103da8e825e8f7676181))
* datahub ([285a9a4](https://github.com/iamgp/phlo/commit/285a9a49ff42dbc5c08e5487500fd280413f3be7))
* datahub ([5678ba9](https://github.com/iamgp/phlo/commit/5678ba909a1c0c0e366def6d4204e603ea057a8e))
* docs ([a9e0d55](https://github.com/iamgp/phlo/commit/a9e0d5547d033e45d9fbbe71329faf12d6ca9a63))
* docs ([2ec7e2b](https://github.com/iamgp/phlo/commit/2ec7e2b9cdcfb9bb7f15a175be6ab698bb3bcb07))
* DuckDB connection pooling and error handling conventions (AUDIT.md tasks 15-16) ([#8](https://github.com/iamgp/phlo/issues/8)) ([9c632ce](https://github.com/iamgp/phlo/commit/9c632ce08f8e0842298549d928dfc3816bcf324e))
* great expectations ([01aab6c](https://github.com/iamgp/phlo/commit/01aab6c273581c84a62fba932dc1fc923cdee542))
* hub ([#1](https://github.com/iamgp/phlo/issues/1)) ([25f5046](https://github.com/iamgp/phlo/commit/25f5046c5e47785a12ffb402d1df23061005735a))
* implement daily partitioning for glucose data (AUDIT.md task 24) ([#11](https://github.com/iamgp/phlo/issues/11)) ([32c00c9](https://github.com/iamgp/phlo/commit/32c00c9cee45b34681a316f6f214df2876fce3ef))
* implement idempotent ingestion with merge/upsert at raw layer ([#17](https://github.com/iamgp/phlo/issues/17)) ([0a286d7](https://github.com/iamgp/phlo/commit/0a286d7bb2ce0dac54bcceeaa8a9ca16cba5dc85))
* **ingestion:** auto-inject metadata columns into ingested data ([8d968fb](https://github.com/iamgp/phlo/commit/8d968fb01e52898171f3f75b5f16dcb10b0038d0))
* initial refactor ([#20](https://github.com/iamgp/phlo/issues/20)) ([95439ab](https://github.com/iamgp/phlo/commit/95439ab8993808e36c34a3b105af20373eabf73b))
* logo ([7d1cd7a](https://github.com/iamgp/phlo/commit/7d1cd7af17e716a3556e9dc4c576df110e0df682))
* marquez ([14ac65f](https://github.com/iamgp/phlo/commit/14ac65f2aa4496315d0fc854fefde2409a13e24e))
* migrate to asset-based Dagster architecture with Airbyte integration ([d4f86ba](https://github.com/iamgp/phlo/commit/d4f86baaf07d6f91ead60ef167dbc6feeacde1e9))
* nightscout airbyte ([b27c985](https://github.com/iamgp/phlo/commit/b27c98510ce4ce2c594aab1458916646ec27cdc7))
* **observability:** implement metrics, alerting, and lineage per spec 005 ([e93832b](https://github.com/iamgp/phlo/commit/e93832b047db8b884510ec2ce80d339dd8961674))
* openmetadata dbt ([e3b512f](https://github.com/iamgp/phlo/commit/e3b512fdf4d7d76d1311fc3aecaf3d8456bd485a))
* PatternCheck and Github helpers ([eefd84c](https://github.com/iamgp/phlo/commit/eefd84c10387fe2d7c3776c4b271e22ed233aebb))
* **plugins:** activate plugin system with CLI and example package per spec 006 ([d0313c9](https://github.com/iamgp/phlo/commit/d0313c94d8bc998324a647f95c76cf315bb8fbeb))
* publish to postgres ([1bfdea0](https://github.com/iamgp/phlo/commit/1bfdea01e7fa6c64bc2724b5f46e0a22d5d1bc56))
* **quality:** implement [@phlo](https://github.com/phlo).quality decorator per spec 003 ([d7d6d0f](https://github.com/iamgp/phlo/commit/d7d6d0fd9f3e7070a664de8d04de01517db0cacd))
* refactor to dlt and partitions ([#12](https://github.com/iamgp/phlo/issues/12)) ([31bda62](https://github.com/iamgp/phlo/commit/31bda62c3a40cd83e4debfb10a67352dd4751ff1))
* **schemas:** add Trino-to-Pandas type mapping utilities ([4ddf133](https://github.com/iamgp/phlo/commit/4ddf133b7618e153531bb24ff5f6b80fe4c81976))
* **testing:** implement testing infrastructure per spec 001 ([0eb39bb](https://github.com/iamgp/phlo/commit/0eb39bb8f463cfcb7239d3bbde9ef4173aeccf88))
* trino password ([7b8ced7](https://github.com/iamgp/phlo/commit/7b8ced783d9f4b23f8f45fbbc1439ab6129dbe07))
* updates ([3be569b](https://github.com/iamgp/phlo/commit/3be569be19d154d277e43af36e4fc7fb80b7dc63))
* updates ([d1ff4ab](https://github.com/iamgp/phlo/commit/d1ff4ab3877a2e57e99a8c271913bfa8519b48b0))
* **validate:** warn when partition_date is declared but unused ([e07909e](https://github.com/iamgp/phlo/commit/e07909e3fe64bf6e063a343d55365e08d28b6b72))


### Bug Fixes

* add automatic schema evolution for new columns in merge_to_table ([f710ab7](https://github.com/iamgp/phlo/commit/f710ab73de917f9ee851e68e3429af9b62efcc2a))
* add column reordering before schema casting in merge_to_table ([f86e038](https://github.com/iamgp/phlo/commit/f86e0387c134836078a4628f2055e925a34eb6c4))
* add per-file ignores and skip dbt-dependent tests in CI ([72dd686](https://github.com/iamgp/phlo/commit/72dd6863ea0e50b0354a70ee3b7bfef31f18879f))
* asset checks ([4c3ea07](https://github.com/iamgp/phlo/commit/4c3ea078ed8ca1873c3b3c8ca8822b8bbfa70980))
* correct DLT usage pattern in workflow development guide ([#16](https://github.com/iamgp/phlo/issues/16)) ([7ddbed2](https://github.com/iamgp/phlo/commit/7ddbed2119d3f1ee5e4bfdfca7968054ef46d5ae))
* correct merge_config parameter in ingestion workflows ([bf8f1d6](https://github.com/iamgp/phlo/commit/bf8f1d6fe0514d09071228b58fe45c7ebe090b8e))
* correct readme.md case to README.md in pyproject.toml ([e9cacf0](https://github.com/iamgp/phlo/commit/e9cacf0e36ec2010f8378e59c6a169973bc44b24))
* dbt transforms for glucose-platform example ([813757f](https://github.com/iamgp/phlo/commit/813757f1f2f1de870c891374d0f5d6b336827003))
* **deps:** update dependency bcrypt to &gt;=4.3.0,&lt;4.4.0 ([#38](https://github.com/iamgp/phlo/issues/38)) ([76904a3](https://github.com/iamgp/phlo/commit/76904a32c811bafe3e3a80d4c61b47b880d01923))
* docker exec working directory and volume mount configuration ([80e9f28](https://github.com/iamgp/phlo/commit/80e9f28477a7a228883d57d8c9f16a3b8b615f27))
* Docker restart resilience and subprocess crashes ([#2](https://github.com/iamgp/phlo/issues/2)) ([dce5e5b](https://github.com/iamgp/phlo/commit/dce5e5b9f3aea56c7988ed534c5537843b5a2603))
* fixes ([e6600ec](https://github.com/iamgp/phlo/commit/e6600ec37f1a80ef12042ca38de015ddf65e1b6c))
* glucose demo ([d3007c2](https://github.com/iamgp/phlo/commit/d3007c21d9d0cabd6e64ca13e09185a9762685af))
* handle ValueError in arrow table casting ([4e7ed11](https://github.com/iamgp/phlo/commit/4e7ed1114e94eb7a020d0914c60bb1ff53b2de62))
* ignore test_quality.py in CI (imports non-existent module) ([e75bad7](https://github.com/iamgp/phlo/commit/e75bad7f8c4e44ceed562f9b77b8e34e716f082b))
* import DbtCliResource at module level for type resolution ([5d20b3d](https://github.com/iamgp/phlo/commit/5d20b3ddceffc5289101be81f835c2fb71ddc6f1))
* improve Nessie sensors and apply ruff formatting ([294bb6d](https://github.com/iamgp/phlo/commit/294bb6d96ef57b3b3eab2ecde1a504b0a6fd78c9))
* linting and type checking issues ([#9](https://github.com/iamgp/phlo/issues/9)) ([d315523](https://github.com/iamgp/phlo/commit/d315523382d365fabc9b40fceb4f8b8b3a195368))
* make sure dbt compile is run ([af4d087](https://github.com/iamgp/phlo/commit/af4d0870286f90f488aa0076f344615cc98d5715))
* mark more tests as integration and format code ([38692b9](https://github.com/iamgp/phlo/commit/38692b988636e0008bf04cf2252e49e0ce759ea1))
* openlineage ([76cffbc](https://github.com/iamgp/phlo/commit/76cffbc0a0fba70efab6c87c8abbbe4923a52754))
* openmetadata trino ([38a8fe1](https://github.com/iamgp/phlo/commit/38a8fe1d7d3912c08e5727f55503fbff97c5a96a))
* ports and datasource ([ca45491](https://github.com/iamgp/phlo/commit/ca45491845bcc5bcab1fc72800f8b3f9d6d6b7a5))
* postgres publish for marts and schema alignment ([f4965f4](https://github.com/iamgp/phlo/commit/f4965f4a4482fc21670dc985772b124aaa9c2950))
* remove GitHub models from glucose-platform example ([820d8aa](https://github.com/iamgp/phlo/commit/820d8aac7693483c8bc53f544f896333d983514e))
* remove type hint from dbt_assets to avoid annotation resolution ([e594d84](https://github.com/iamgp/phlo/commit/e594d847c5d77498d2712cf73d45c3cf7828a18f))
* repair 12 failing unit tests ([cfdbd29](https://github.com/iamgp/phlo/commit/cfdbd2907fe95182cd59103a827e5727ababe3ec))
* resolve Generator type annotation error in dbt discovery ([93d6a33](https://github.com/iamgp/phlo/commit/93d6a33a97fdf19e711ffedf73cf1257b8cade98))
* resolve lint errors for CI ([92464e9](https://github.com/iamgp/phlo/commit/92464e9dc2f46e7b88bd16d0b5bcf777a318dfc7))
* resolve type-check and sql-lint errors ([f89e922](https://github.com/iamgp/phlo/commit/f89e92280368b21a8366ba8dc5386afa32ea4fae))
* superset ([c85199f](https://github.com/iamgp/phlo/commit/c85199f05713182affb896f64e5bcbc042331478))
* superset setup ([9ee5ba6](https://github.com/iamgp/phlo/commit/9ee5ba67f0becd1c77ee2a1fbfe8707598d5748f))
* update pyiceberg expression import from IsIn to In ([425ad96](https://github.com/iamgp/phlo/commit/425ad963ae6e8cd4e8603c865510ca7860c206cd))
* use versioning prerelease for alpha releases ([12f42c0](https://github.com/iamgp/phlo/commit/12f42c0248be75bd7613cddb810bf9b497083d21))


### Documentation

* add badges, update install to use uv/PyPI ([4ca62ed](https://github.com/iamgp/phlo/commit/4ca62ed025deeaaf0588a6a4a1f58ddb11feb53e))
* add comprehensive audit compliance review ([#27](https://github.com/iamgp/phlo/issues/27)) ([3ee5972](https://github.com/iamgp/phlo/commit/3ee5972ea0f7c76f4cbf6a28dd58d0746194c60e))
* add comprehensive documentation for all components ([9159480](https://github.com/iamgp/phlo/commit/915948098cb5e25213dd0e989bf5199e4477ec64))
* add comprehensive plan for making Cascade an installable package ([#29](https://github.com/iamgp/phlo/issues/29)) ([06dd402](https://github.com/iamgp/phlo/commit/06dd4027bb824142e58ec9c69ed47a7bc3313e85))
* add comprehensive PRD for FastAPI to PostgREST migration ([#28](https://github.com/iamgp/phlo/issues/28)) ([70f4113](https://github.com/iamgp/phlo/commit/70f4113a49ea9d82792c717c282abc83d9a69da8))
* address AUDIT.md tasks 17-22 ([#10](https://github.com/iamgp/phlo/issues/10)) ([c3c7f16](https://github.com/iamgp/phlo/commit/c3c7f1604583a7415483c7c05b9354ea7657fdea))
* clean up and reorganize documentation ([e5bb0f0](https://github.com/iamgp/phlo/commit/e5bb0f040786c7b2ddb4b1e07899262b7afc4ad5))
* comprehensive usability audit with recommendations ([#22](https://github.com/iamgp/phlo/issues/22)) ([d0fa942](https://github.com/iamgp/phlo/commit/d0fa942ab11b435fff74f0207780743fad89fa70))
* **examples:** add complete test examples using phlo_testing fixtures ([db86e99](https://github.com/iamgp/phlo/commit/db86e99531edcf8c635d281d433fb1209865b120))
* fix weather example to use DLT and add documentation index ([#15](https://github.com/iamgp/phlo/issues/15)) ([de1bcc2](https://github.com/iamgp/phlo/commit/de1bcc2d0ccd4299f21039ec3d9932bbfc4bdd88))
* refactor README to follow best practices ([#25](https://github.com/iamgp/phlo/issues/25)) ([0b49d77](https://github.com/iamgp/phlo/commit/0b49d77f65f41fc717541dd11b34805b5fe14b7e))
* remove license badge ([a1ce339](https://github.com/iamgp/phlo/commit/a1ce339b54e93ec04a6b27e5a5e3f5e1a4f50f07))
* reorganize documentation into logical directory structure ([#26](https://github.com/iamgp/phlo/issues/26)) ([51e82d9](https://github.com/iamgp/phlo/commit/51e82d966ec0d237bd2f9c4295e22f955f53787b))
* simplify README and move planning docs to specs/ ([1354039](https://github.com/iamgp/phlo/commit/13540395cf2d2ef1c2469c06f88334c22226a35f))
* update blog posts with correct Nessie branching and WAP pattern ([59f7b95](https://github.com/iamgp/phlo/commit/59f7b955f16a28c1cfac2b02b32823bc6f05cbe1))
* update blog posts with current examples ([#33](https://github.com/iamgp/phlo/issues/33)) ([1b5ac3f](https://github.com/iamgp/phlo/commit/1b5ac3f95222c7b8583129bc66d08ffdf28657bb))


### Code Refactoring

* ([#13](https://github.com/iamgp/phlo/issues/13)) ([e58b896](https://github.com/iamgp/phlo/commit/e58b896cd53448bd90a45411563251a395ed4e3e))
