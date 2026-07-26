FROM postgrest/postgrest:v14.15@sha256:2f8e7b656f09db697a8875177694b417b35cb76c21370de07fc54e711e902326 AS upstream

FROM ubuntu:26.04@sha256:3131b4cc82a783df6c9df078f86e01819a13594b865c2cad47bd1bca2b7063bb

# Install the repository's current security revisions instead of freezing stale package versions.
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get upgrade --yes && \
    apt-get install --yes --no-install-recommends \
        ca-certificates \
        libgmp10 \
        libpq5 \
        procps && \
    rm -f /usr/bin/pebble && \
    rm -rf /var/lib/apt/lists/*

COPY --from=upstream /bin/postgrest /usr/bin/postgrest

USER "1000"
EXPOSE 3000
CMD ["postgrest"]
