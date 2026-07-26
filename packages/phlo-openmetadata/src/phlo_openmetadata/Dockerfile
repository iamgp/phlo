FROM alpine:3.24.1@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b AS patches

SHELL ["/bin/ash", "-o", "pipefail", "-c"]
RUN apk add --no-cache curl=8.21.0-r0
WORKDIR /patches
RUN set -eux; \
    for artifact in \
        netty-buffer \
        netty-codec \
        netty-codec-dns \
        netty-codec-http \
        netty-codec-http2 \
        netty-codec-socks \
        netty-common \
        netty-handler \
        netty-handler-proxy \
        netty-resolver \
        netty-resolver-dns \
        netty-resolver-dns-classes-macos \
        netty-transport \
        netty-transport-classes-epoll \
        netty-transport-classes-kqueue \
        netty-transport-native-unix-common; do \
      file="${artifact}-4.1.136.Final.jar"; \
      base="https://repo1.maven.org/maven2/io/netty/${artifact}/4.1.136.Final/${file}"; \
      curl --fail --location --silent --show-error "$base" --output "$file"; \
      curl --fail --location --silent --show-error "$base.sha256" --output "$file.sha256"; \
      echo "$(cat "$file.sha256")  $file" | sha256sum -c -; \
    done
RUN curl --fail --location --silent --show-error \
        https://repo1.maven.org/maven2/org/eclipse/jetty/jetty-security/12.1.10/jetty-security-12.1.10.jar \
        --output jetty-security-12.1.10.jar && \
    echo "2f34b7895cec4e3547a1b52e12e7e92b3f3a110bf3c17637f8743ca3f4e42f0c  jetty-security-12.1.10.jar" | sha256sum -c -
RUN curl --fail --location --silent --show-error \
        https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.13/postgresql-42.7.13.jar \
        --output postgresql-42.7.13.jar && \
    echo "6e0e4cc2d8cae902084f8a2b18728b073a6fd9d1f87c9d8bff8f298c18185b93  postgresql-42.7.13.jar" | sha256sum -c -

FROM docker.getcollate.io/openmetadata/server:1.13.1@sha256:eaa318584c52d4a492a2c56c95818b5564c6ea28b2e9695ac532c856b2c61bc9

USER root
RUN rm /opt/openmetadata/libs/netty-*-4.1.135.Final.jar \
        /opt/openmetadata/libs/jetty-security-12.1.1.jar \
        /opt/openmetadata/libs/postgresql-42.7.11.jar
COPY --from=patches --chown=openmetadata:openmetadata /patches/*.jar /opt/openmetadata/libs/

USER openmetadata
