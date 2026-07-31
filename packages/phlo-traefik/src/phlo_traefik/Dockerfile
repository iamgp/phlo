FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS build

RUN apk add --no-cache git=2.54.0-r0
WORKDIR /src
RUN git clone --depth 1 --branch v3.7.10 https://github.com/traefik/traefik.git . && \
    git checkout --detach 2a2349356c01b1b1f7ecddb0c17b30c97f5241e7 && \
    CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o /traefik ./cmd/traefik

FROM alpine:3.24

RUN apk add --no-cache --no-progress ca-certificates tzdata
COPY --from=build /traefik /traefik

EXPOSE 80
VOLUME ["/tmp"]

ENTRYPOINT ["/traefik"]
