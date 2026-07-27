FROM alpine:3.23@sha256:fd791d74b68913cbb027c6546007b3f0d3bc45125f797758156952bc2d6daf40 AS patches

RUN apk add --no-cache curl=8.20.0-r0
WORKDIR /patches
RUN for artifact in \
      netty-buffer netty-codec netty-codec-dns netty-codec-http \
      netty-codec-http2 netty-codec-socks netty-common netty-handler \
      netty-handler-proxy netty-resolver netty-resolver-dns netty-transport \
      netty-transport-native-unix-common; do \
        curl --fail --silent --show-error --location \
          "https://repo1.maven.org/maven2/io/netty/${artifact}/4.1.136.Final/${artifact}-4.1.136.Final.jar" \
          --output "${artifact}-4.1.136.Final.jar"; \
    done && \
    curl --fail --silent --show-error --location \
      https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-annotations/2.18.8/jackson-annotations-2.18.8.jar \
      --output jackson-annotations-2.18.8.jar && \
    curl --fail --silent --show-error --location \
      https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/2.18.8/jackson-core-2.18.8.jar \
      --output jackson-core-2.18.8.jar && \
    curl --fail --silent --show-error --location \
      https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.18.8/jackson-databind-2.18.8.jar \
      --output jackson-databind-2.18.8.jar && \
    curl --fail --silent --show-error --location \
      https://repo1.maven.org/maven2/com/fasterxml/jackson/dataformat/jackson-dataformat-cbor/2.18.8/jackson-dataformat-cbor-2.18.8.jar \
      --output jackson-dataformat-cbor-2.18.8.jar && \
    curl --fail --silent --show-error --location \
      https://repo1.maven.org/maven2/com/fasterxml/jackson/dataformat/jackson-dataformat-xml/2.18.8/jackson-dataformat-xml-2.18.8.jar \
      --output jackson-dataformat-xml-2.18.8.jar && \
    curl --fail --silent --show-error --location \
      https://repo1.maven.org/maven2/com/fasterxml/jackson/datatype/jackson-datatype-jsr310/2.18.8/jackson-datatype-jsr310-2.18.8.jar \
      --output jackson-datatype-jsr310-2.18.8.jar && \
    curl --fail --silent --show-error --location \
      https://repo1.maven.org/maven2/com/fasterxml/jackson/module/jackson-module-jaxb-annotations/2.18.8/jackson-module-jaxb-annotations-2.18.8.jar \
      --output jackson-module-jaxb-annotations-2.18.8.jar && \
    curl --fail --silent --show-error --location \
      https://repo1.maven.org/maven2/com/google/protobuf/protobuf-java/3.25.5/protobuf-java-3.25.5.jar \
      --output protobuf-java-3.25.5.jar && \
    curl --fail --silent --show-error --location \
      https://repo1.maven.org/maven2/com/nimbusds/nimbus-jose-jwt/9.37.2/nimbus-jose-jwt-9.37.2.jar \
      --output nimbus-jose-jwt-9.37.2.jar && \
    curl --fail --silent --show-error --location \
      https://repo1.maven.org/maven2/commons-io/commons-io/2.14.0/commons-io-2.14.0.jar \
      --output commons-io-2.14.0.jar
COPY openmetadata-elasticsearch/libraries.sha256 libraries.sha256
RUN sha256sum -c libraries.sha256

FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.4@sha256:8425bc28027fd667d9a29cde58bed4050a64a854d973d8d1ad4152ecec52bfdb

COPY --from=patches /patches/commons-io-2.14.0.jar /usr/share/elasticsearch/modules/ingest-attachment/commons-io-2.11.0.jar
COPY --from=patches /patches/protobuf-java-3.25.5.jar /usr/share/elasticsearch/modules/repository-gcs/protobuf-java-3.21.9.jar
COPY --from=patches /patches/protobuf-java-3.25.5.jar /usr/share/elasticsearch/modules/vector-tile/protobuf-java-3.21.9.jar
COPY --from=patches /patches/nimbus-jose-jwt-9.37.2.jar /usr/share/elasticsearch/modules/x-pack-security/nimbus-jose-jwt-9.23.jar

COPY --from=patches /patches/jackson-annotations-2.18.8.jar /usr/share/elasticsearch/modules/ingest-geoip/jackson-annotations-2.15.0.jar
COPY --from=patches /patches/jackson-core-2.18.8.jar /usr/share/elasticsearch/modules/ingest-geoip/jackson-core-2.15.0.jar
COPY --from=patches /patches/jackson-databind-2.18.8.jar /usr/share/elasticsearch/modules/ingest-geoip/jackson-databind-2.15.0.jar
COPY --from=patches /patches/jackson-core-2.18.8.jar /usr/share/elasticsearch/modules/legacy-geo/jackson-core-2.15.0.jar
COPY --from=patches /patches/jackson-annotations-2.18.8.jar /usr/share/elasticsearch/modules/repository-azure/jackson-annotations-2.13.4.jar
COPY --from=patches /patches/jackson-core-2.18.8.jar /usr/share/elasticsearch/modules/repository-azure/jackson-core-2.13.4.jar
COPY --from=patches /patches/jackson-databind-2.18.8.jar /usr/share/elasticsearch/modules/repository-azure/jackson-databind-2.13.4.2.jar
COPY --from=patches /patches/jackson-dataformat-xml-2.18.8.jar /usr/share/elasticsearch/modules/repository-azure/jackson-dataformat-xml-2.13.4.jar
COPY --from=patches /patches/jackson-datatype-jsr310-2.18.8.jar /usr/share/elasticsearch/modules/repository-azure/jackson-datatype-jsr310-2.13.4.jar
COPY --from=patches /patches/jackson-module-jaxb-annotations-2.18.8.jar /usr/share/elasticsearch/modules/repository-azure/jackson-module-jaxb-annotations-2.13.4.jar
COPY --from=patches /patches/jackson-core-2.18.8.jar /usr/share/elasticsearch/modules/repository-gcs/jackson-core-2.15.0.jar
COPY --from=patches /patches/jackson-annotations-2.18.8.jar /usr/share/elasticsearch/modules/repository-s3/jackson-annotations-2.15.0.jar
COPY --from=patches /patches/jackson-core-2.18.8.jar /usr/share/elasticsearch/modules/repository-s3/jackson-core-2.15.0.jar
COPY --from=patches /patches/jackson-databind-2.18.8.jar /usr/share/elasticsearch/modules/repository-s3/jackson-databind-2.15.0.jar
COPY --from=patches /patches/jackson-dataformat-cbor-2.18.8.jar /usr/share/elasticsearch/modules/repository-s3/jackson-dataformat-cbor-2.15.0.jar
COPY --from=patches /patches/jackson-annotations-2.18.8.jar /usr/share/elasticsearch/modules/x-pack-ent-search/jackson-annotations-2.15.0.jar
COPY --from=patches /patches/jackson-core-2.18.8.jar /usr/share/elasticsearch/modules/x-pack-ent-search/jackson-core-2.15.0.jar
COPY --from=patches /patches/jackson-databind-2.18.8.jar /usr/share/elasticsearch/modules/x-pack-ent-search/jackson-databind-2.15.0.jar
COPY --from=patches /patches/jackson-core-2.18.8.jar /usr/share/elasticsearch/modules/x-pack-monitoring/jackson-core-2.15.0.jar
COPY --from=patches /patches/jackson-core-2.18.8.jar /usr/share/elasticsearch/modules/x-pack-sql/jackson-core-2.15.0.jar
COPY --from=patches /patches/jackson-dataformat-cbor-2.18.8.jar /usr/share/elasticsearch/modules/x-pack-sql/jackson-dataformat-cbor-2.15.0.jar

COPY --from=patches /patches/netty-buffer-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-buffer-4.1.94.Final.jar
COPY --from=patches /patches/netty-codec-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-codec-4.1.94.Final.jar
COPY --from=patches /patches/netty-codec-dns-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-codec-dns-4.1.94.Final.jar
COPY --from=patches /patches/netty-codec-http-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-codec-http-4.1.94.Final.jar
COPY --from=patches /patches/netty-codec-http2-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-codec-http2-4.1.94.Final.jar
COPY --from=patches /patches/netty-codec-socks-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-codec-socks-4.1.94.Final.jar
COPY --from=patches /patches/netty-common-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-common-4.1.94.Final.jar
COPY --from=patches /patches/netty-handler-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-handler-4.1.94.Final.jar
COPY --from=patches /patches/netty-handler-proxy-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-handler-proxy-4.1.94.Final.jar
COPY --from=patches /patches/netty-resolver-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-resolver-4.1.94.Final.jar
COPY --from=patches /patches/netty-resolver-dns-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-resolver-dns-4.1.94.Final.jar
COPY --from=patches /patches/netty-transport-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-transport-4.1.94.Final.jar
COPY --from=patches /patches/netty-transport-native-unix-common-4.1.136.Final.jar /usr/share/elasticsearch/modules/repository-azure/netty-transport-native-unix-common-4.1.94.Final.jar

COPY --from=patches /patches/netty-buffer-4.1.136.Final.jar /usr/share/elasticsearch/modules/transport-netty4/netty-buffer-4.1.94.Final.jar
COPY --from=patches /patches/netty-codec-4.1.136.Final.jar /usr/share/elasticsearch/modules/transport-netty4/netty-codec-4.1.94.Final.jar
COPY --from=patches /patches/netty-codec-http-4.1.136.Final.jar /usr/share/elasticsearch/modules/transport-netty4/netty-codec-http-4.1.94.Final.jar
COPY --from=patches /patches/netty-common-4.1.136.Final.jar /usr/share/elasticsearch/modules/transport-netty4/netty-common-4.1.94.Final.jar
COPY --from=patches /patches/netty-handler-4.1.136.Final.jar /usr/share/elasticsearch/modules/transport-netty4/netty-handler-4.1.94.Final.jar
COPY --from=patches /patches/netty-resolver-4.1.136.Final.jar /usr/share/elasticsearch/modules/transport-netty4/netty-resolver-4.1.94.Final.jar
COPY --from=patches /patches/netty-transport-4.1.136.Final.jar /usr/share/elasticsearch/modules/transport-netty4/netty-transport-4.1.94.Final.jar
COPY --from=patches /patches/netty-transport-native-unix-common-4.1.136.Final.jar /usr/share/elasticsearch/modules/transport-netty4/netty-transport-native-unix-common-4.1.94.Final.jar

COPY --from=patches /patches/netty-buffer-4.1.136.Final.jar /usr/share/elasticsearch/modules/x-pack-security/netty-buffer-4.1.94.Final.jar
COPY --from=patches /patches/netty-codec-4.1.136.Final.jar /usr/share/elasticsearch/modules/x-pack-security/netty-codec-4.1.94.Final.jar
COPY --from=patches /patches/netty-codec-http-4.1.136.Final.jar /usr/share/elasticsearch/modules/x-pack-security/netty-codec-http-4.1.94.Final.jar
COPY --from=patches /patches/netty-common-4.1.136.Final.jar /usr/share/elasticsearch/modules/x-pack-security/netty-common-4.1.94.Final.jar
COPY --from=patches /patches/netty-handler-4.1.136.Final.jar /usr/share/elasticsearch/modules/x-pack-security/netty-handler-4.1.94.Final.jar
COPY --from=patches /patches/netty-resolver-4.1.136.Final.jar /usr/share/elasticsearch/modules/x-pack-security/netty-resolver-4.1.94.Final.jar
COPY --from=patches /patches/netty-transport-4.1.136.Final.jar /usr/share/elasticsearch/modules/x-pack-security/netty-transport-4.1.94.Final.jar
COPY --from=patches /patches/netty-transport-native-unix-common-4.1.136.Final.jar /usr/share/elasticsearch/modules/x-pack-security/netty-transport-native-unix-common-4.1.94.Final.jar

USER "0"
RUN find /usr/share/elasticsearch/modules -name 'jackson-core-2.15.0.jar' \
      -exec sh -c 'for path do mv "$path" "${path%/*}/jackson-core-2.18.8.jar"; done' sh {} +

USER "1000"
