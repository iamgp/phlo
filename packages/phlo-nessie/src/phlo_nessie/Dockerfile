FROM eclipse-temurin:21-jdk-alpine@sha256:1ff763083f2993d57d0bf374ab10bb3e2cb873af6c13a04458ebbd3e0337dc76 AS build

RUN apk add --no-cache bash=5.3.3-r1 curl=8.20.0-r0 git=2.52.0-r0
WORKDIR /src
RUN git clone https://github.com/projectnessie/nessie.git . && \
    git checkout b715f4374d69e68bcfac0e359bf2dd55875b3e25
RUN ./gradlew --no-daemon :nessie-quarkus:quarkusBuild -x check
RUN mkdir /patches && \
    for artifact in \
      netty-buffer netty-codec netty-codec-dns netty-codec-haproxy \
      netty-codec-http netty-codec-http2 netty-codec-socks netty-common \
      netty-handler netty-handler-proxy netty-resolver netty-resolver-dns \
      netty-resolver-dns-classes-macos netty-transport \
      netty-transport-classes-epoll netty-transport-classes-kqueue \
      netty-transport-native-unix-common; do \
        curl --fail --silent --show-error --location \
          "https://repo1.maven.org/maven2/io/netty/${artifact}/4.1.136.Final/${artifact}-4.1.136.Final.jar" \
          --output "/patches/io.netty.${artifact}-4.1.136.Final.jar"; \
    done && \
    curl --fail --silent --show-error --location \
      "https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/2.22.1/jackson-core-2.22.1.jar" \
      --output /patches/com.fasterxml.jackson.core.jackson-core-2.22.1.jar
COPY libraries.sha256 /patches/libraries.sha256
WORKDIR /patches
RUN sha256sum --check libraries.sha256 && \
    for artifact in io.netty.*-4.1.136.Final.jar; do \
      mv "${artifact}" "${artifact%-4.1.136.Final.jar}-4.1.135.Final.jar"; \
    done && \
    mv com.fasterxml.jackson.core.jackson-core-2.22.1.jar \
      com.fasterxml.jackson.core.jackson-core-2.22.0.jar

FROM eclipse-temurin:21-jre-alpine@sha256:3f08b13888f595cc49edabea7250ba69499ba25602b267da591720769400e08c

RUN apk upgrade --no-cache && \
    apk add --no-cache curl=8.20.0-r0 && \
    addgroup -g 10001 nessie && \
    adduser -D -u 10000 -G nessie -h /home/nessie -s /sbin/nologin nessie
COPY --from=build --chown=nessie:nessie /src/servers/quarkus-server/build/quarkus-app/ /deployments/
COPY --from=build --chown=nessie:nessie /patches/*.jar /deployments/lib/main/

ENV HOME=/home/nessie
USER nessie
EXPOSE 19120
ENTRYPOINT ["java", "-jar", "/deployments/quarkus-run.jar"]
