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
RUN CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o /esbuild ./cmd/esbuild
WORKDIR /src
RUN git clone --branch v4.3.3 --depth 1 https://github.com/hairyhenderson/gomplate.git
WORKDIR /src/gomplate
RUN go get \
      github.com/go-git/go-billy/v5@v5.9.0 \
      github.com/go-git/go-git/v5@v5.19.0 \
      github.com/go-jose/go-jose/v4@v4.1.4 \
      go.opentelemetry.io/otel@v1.43.0 \
      go.opentelemetry.io/otel/sdk@v1.43.0 \
      golang.org/x/crypto@v0.52.0 \
      golang.org/x/net@v0.55.0 \
      google.golang.org/grpc@v1.82.1 \
    && CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o /gomplate ./cmd/gomplate

FROM docker.io/hyperdx/hyperdx-all-in-one:2.31.0@sha256:b01cc48cb5aaf30d630865a88217c826ab86fb9828374201f6cd7c539d5beed1

RUN apk update \
    && apk upgrade --no-cache --available \
    && rm -f /usr/local/bin/goose

COPY --from=go-patches /esbuild /tmp/esbuild
COPY --from=go-patches /gomplate /usr/local/bin/gomplate
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
