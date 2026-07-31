FROM node:22.22-alpine@sha256:e58326d0d441090181ac150dc2078d3e2cf6a0d42e809aebba3ef5880935ffdd AS node-patches

RUN npm install --prefix /patches \
      axios@1.18.0 \
      brace-expansion@2.1.2 \
      fast-uri@3.1.4 \
      immutable@4.3.9 \
      js-yaml@4.3.0 \
      minimatch@3.1.4 \
      path-to-regexp@0.1.13 \
      protobufjs@7.6.1 \
      serialize-javascript@7.0.3 \
      sharp@0.35.0 \
      shell-quote@1.9.0 \
      systeminformation@5.31.7 \
      validator@13.15.22

FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS go-patches

RUN apk add --no-cache git=2.54.0-r0
WORKDIR /src
RUN git clone --branch v0.25.1 --depth 1 https://github.com/evanw/esbuild.git
WORKDIR /src/esbuild
RUN go get golang.org/x/text@v0.39.0 && \
    CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o /esbuild ./cmd/esbuild
WORKDIR /src
RUN git clone --branch v4.3.3 --depth 1 https://github.com/hairyhenderson/gomplate.git
WORKDIR /src/gomplate
RUN go get \
      github.com/go-git/go-billy/v5@v5.9.0 \
      github.com/go-git/go-git/v5@v5.19.0 \
      github.com/go-jose/go-jose/v4@v4.1.4 \
      go.opentelemetry.io/otel@v1.43.0 \
      go.opentelemetry.io/otel/sdk@v1.43.0 \
      golang.org/x/crypto@v0.53.0 \
      golang.org/x/net@v0.56.0 \
      golang.org/x/text@v0.39.0 \
      google.golang.org/grpc@v1.82.1 \
    && CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o /gomplate ./cmd/gomplate

# HyperDX packages its OpenTelemetry collector inside the all-in-one image. Build
# the exact collector source used by the 2.32.0 release with patched Go modules,
# then replace only that embedded binary in the final image.
FROM otel/opentelemetry-collector-builder:0.155.0 AS otel-builder

FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS hyperdx-otel-patches

RUN apk add --no-cache git=2.54.0-r0
COPY --from=otel-builder /usr/local/bin/ocb /usr/local/bin/ocb
WORKDIR /src
RUN git clone --depth 1 https://github.com/hyperdxio/hyperdx.git hyperdx && \
    git -C hyperdx fetch --depth 1 origin 31a461db46d23439c4b72c80be02d6991e924921 && \
    git -C hyperdx checkout --detach 31a461db46d23439c4b72c80be02d6991e924921
WORKDIR /build
RUN cp /src/hyperdx/packages/otel-collector/builder-config.yaml . && \
    sed -i 's/__OTEL_COLLECTOR_VERSION__/0.155.0/g; s/__OTEL_COLLECTOR_CORE_VERSION__/1.61.0/g' builder-config.yaml && \
    CGO_ENABLED=0 ocb --config=builder-config.yaml && \
    cd output && \
    go get \
      golang.org/x/crypto@v0.53.0 \
      golang.org/x/net@v0.56.0 \
      golang.org/x/text@v0.39.0 \
      google.golang.org/grpc@v1.82.1 && \
    go mod tidy && \
    CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o /otelcontribcol .

FROM docker.io/hyperdx/hyperdx-all-in-one:2.32.0@sha256:54a0a805d761d6fef76122736a0d62400b78f69bd00394fe15086c8eda39b6c7

RUN apk update \
    && apk upgrade --no-cache --available \
    && rm -f /usr/local/bin/goose

COPY --from=go-patches /esbuild /tmp/esbuild
COPY --from=go-patches /gomplate /usr/local/bin/gomplate
COPY --from=hyperdx-otel-patches /otelcontribcol /otelcontribcol
RUN find /app/packages/app/node_modules/@esbuild -path '*/bin/esbuild' \
      -exec install -m 0755 /tmp/esbuild {} \; \
    && rm /tmp/esbuild
COPY --from=node-patches /patches/node_modules/axios /app/node_modules/axios
COPY --from=node-patches /patches/node_modules/axios /app/packages/app/node_modules/axios
COPY --from=node-patches /patches/node_modules/brace-expansion /app/packages/app/node_modules/brace-expansion
COPY --from=node-patches /patches/node_modules/fast-uri /app/node_modules/fast-uri
COPY --from=node-patches /patches/node_modules/fast-uri /app/packages/app/node_modules/fast-uri
COPY --from=node-patches /patches/node_modules/immutable /app/packages/app/node_modules/immutable
COPY --from=node-patches /patches/node_modules/js-yaml /app/packages/app/node_modules/@apidevtools/json-schema-ref-parser/node_modules/js-yaml
COPY --from=node-patches /patches/node_modules/minimatch /app/packages/app/node_modules/minimatch
COPY --from=node-patches /patches/node_modules/path-to-regexp /app/node_modules/path-to-regexp
COPY --from=node-patches /patches/node_modules/path-to-regexp /app/packages/app/node_modules/path-to-regexp
COPY --from=node-patches /patches/node_modules/protobufjs /app/node_modules/@opentelemetry/otlp-transformer/node_modules/protobufjs
COPY --from=node-patches /patches/node_modules/protobufjs /app/packages/app/node_modules/@opentelemetry/otlp-transformer/node_modules/protobufjs
COPY --from=node-patches /patches/node_modules/serialize-javascript /app/packages/app/node_modules/serialize-javascript
COPY --from=node-patches /patches/node_modules/sharp /app/packages/app/node_modules/sharp
COPY --from=node-patches /patches/node_modules/shell-quote /app/node_modules/shell-quote
COPY --from=node-patches /patches/node_modules/systeminformation /app/node_modules/systeminformation
COPY --from=node-patches /patches/node_modules/validator /app/packages/app/node_modules/validator

# hadolint ignore=DL3002
USER "0"
