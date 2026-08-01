FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS build

RUN apk add --no-cache git=2.54.0-r0
WORKDIR /src
RUN git clone https://github.com/prometheus/prometheus.git . && \
    git checkout 73ff57ce2b8161059ac7fe5188f03f1c3d22b29a && \
    go get google.golang.org/grpc@v1.82.1 golang.org/x/text@v0.39.0
RUN LDFLAGS="-s -w -X github.com/prometheus/common/version.Version=3.13.1 -X github.com/prometheus/common/version.Revision=73ff57ce2b8161059ac7fe5188f03f1c3d22b29a" && \
    CGO_ENABLED=0 go build -trimpath -ldflags="$LDFLAGS" -o /out/prometheus ./cmd/prometheus && \
    CGO_ENABLED=0 go build -trimpath -ldflags="$LDFLAGS" -o /out/promtool ./cmd/promtool

FROM prom/prometheus:v3.13.1@sha256:3c42b892cf723fa54d2f262c37a0e1f80aa8c8ddb1da7b9b0df9455a35a7f893

COPY --from=build /out/prometheus /bin/prometheus
COPY --from=build /out/promtool /bin/promtool

USER nobody
