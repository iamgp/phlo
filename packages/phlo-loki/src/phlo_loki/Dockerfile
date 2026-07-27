FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS build

RUN apk add --no-cache git=2.54.0-r0
RUN git clone https://github.com/grafana/loki.git /src/loki && \
    git -C /src/loki checkout b318f2829f0ae2094ab3a1e90780450e9e4b03be
WORKDIR /src/loki
RUN go get google.golang.org/grpc@v1.82.1 && go mod tidy
RUN CGO_ENABLED=0 go build -mod=mod -trimpath -tags netgo \
    -ldflags="-s -w \
        -X github.com/grafana/loki/v3/pkg/util/build.Branch=release-3.7.x \
        -X github.com/grafana/loki/v3/pkg/util/build.Version=3.7.4 \
        -X github.com/grafana/loki/v3/pkg/util/build.Revision=b318f2829f0ae2094ab3a1e90780450e9e4b03be" \
    -o /out/loki ./cmd/loki

FROM grafana/loki:3.7.4@sha256:87f0a067673756a3cede1bcbf0c74875f7df9b09fddb53e399d0c576f756cfcc

COPY --from=build /out/loki /usr/bin/loki

USER 10001
