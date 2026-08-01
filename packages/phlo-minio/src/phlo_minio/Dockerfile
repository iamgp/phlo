FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS build

RUN apk add --no-cache git=2.54.0-r0
WORKDIR /src
RUN git clone https://github.com/minio/minio.git . && \
    git checkout 7aac2a2c5b7c882e68c1ce017d8256be2feea27f && \
    go get \
        github.com/apache/thrift@v0.23.0 \
        github.com/buger/jsonparser@v1.1.2 \
        github.com/go-jose/go-jose/v4@v4.1.4 \
        github.com/prometheus/prometheus@v0.311.3 \
        go.opentelemetry.io/otel/sdk@v1.43.0 \
        golang.org/x/crypto@v0.52.0 \
        golang.org/x/net@v0.55.0 \
        golang.org/x/text@v0.39.0 \
        google.golang.org/grpc@v1.82.1 && \
    go mod tidy -e
# hadolint ignore=DL3062
RUN LDFLAGS="$(go run buildscripts/gen-ldflags.go)" && \
    CGO_ENABLED=0 go build -tags kqueue -trimpath -ldflags="$LDFLAGS -s -w" -o /out/minio .

FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS mc-build

RUN apk add --no-cache git=2.54.0-r0
WORKDIR /src
RUN git clone https://github.com/minio/mc.git . && \
    git checkout 77f82e18b5401a65958f1619df6ebb994634bd88 && \
    go get \
        github.com/prometheus/prometheus@v0.311.3 \
        golang.org/x/crypto@v0.52.0 \
        golang.org/x/net@v0.55.0 \
        golang.org/x/text@v0.39.0 \
        google.golang.org/grpc@v1.82.1 && \
    go mod tidy
# hadolint ignore=DL3062
RUN LDFLAGS="$(go run buildscripts/gen-ldflags.go)" && \
    CGO_ENABLED=0 go build -tags kqueue -trimpath -ldflags="$LDFLAGS -s -w" -o /out/mc .

FROM alpine:3.22.5@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce

RUN apk upgrade --no-cache && \
    apk add --no-cache ca-certificates=20260611-r0 curl=8.14.1-r3 && \
    adduser -D -h /home/minio -s /sbin/nologin minio && \
    mkdir /data && \
    chown minio:minio /data
COPY --from=build /out/minio /usr/bin/minio
COPY --from=mc-build /out/mc /usr/bin/mc

ENV HOME=/home/minio
USER minio
EXPOSE 9000 9001
ENTRYPOINT ["/usr/bin/minio"]
