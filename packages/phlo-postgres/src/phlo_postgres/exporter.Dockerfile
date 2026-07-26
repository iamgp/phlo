FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS build

RUN apk add --no-cache git=2.54.0-r0
WORKDIR /src
RUN git clone https://github.com/prometheus-community/postgres_exporter.git . && \
    git checkout 867fbcac31cd18c143e244190ea9168cca069827
RUN CGO_ENABLED=0 go build -trimpath \
    -ldflags="-s -w -X github.com/prometheus/common/version.Version=0.20.1 -X github.com/prometheus/common/version.Revision=867fbcac31cd18c143e244190ea9168cca069827" \
    -o /out/postgres_exporter ./cmd/postgres_exporter

FROM quay.io/prometheuscommunity/postgres-exporter:v0.20.1@sha256:ac5ec343104fae0e2d84a27bb8d69b38430a11910c5382cad85d478d2bab713e

COPY --from=build /out/postgres_exporter /bin/postgres_exporter
