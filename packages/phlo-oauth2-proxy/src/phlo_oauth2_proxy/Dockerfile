FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS build

RUN apk add --no-cache git=2.54.0-r0
WORKDIR /src
RUN git clone https://github.com/oauth2-proxy/oauth2-proxy.git . && \
    git checkout 66b3a17db09f0b51a4bc3159d4c7fe3fbeca1288 && \
    go get google.golang.org/grpc@v1.82.1 \
        google.golang.org/x/text@v0.39.0
RUN CGO_ENABLED=0 go build -trimpath \
    -ldflags="-s -w -X github.com/oauth2-proxy/oauth2-proxy/v7/pkg/version.VERSION=v7.15.3" \
    -o /out/oauth2-proxy .
COPY oauth2-proxy/oauth2_proxy_healthcheck.go /tmp/oauth2_proxy_healthcheck.go
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" \
    -o /out/oauth2-proxy-healthcheck /tmp/oauth2_proxy_healthcheck.go

FROM quay.io/oauth2-proxy/oauth2-proxy:v7.15.3@sha256:10a1165743a192e1940b4708fb9647027185ce11a681a1c5519b442ff7f1f561

COPY --from=build /out/oauth2-proxy /bin/oauth2-proxy
COPY --from=build /out/oauth2-proxy-healthcheck /bin/oauth2-proxy-healthcheck

USER 65532
