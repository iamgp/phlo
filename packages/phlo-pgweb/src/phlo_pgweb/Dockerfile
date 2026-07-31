FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS build

RUN apk add --no-cache git=2.54.0-r0
WORKDIR /src
RUN git clone --depth 1 --branch v0.17.0 https://github.com/sosedoff/pgweb.git . && \
    git checkout 6b0b0244d1aefd6971999b03481eeeaa4ec7cf55 && \
    go get github.com/sirupsen/logrus@v1.9.3 golang.org/x/crypto@v0.52.0 golang.org/x/net@v0.55.0 golang.org/x/text@v0.39.0 && \
    go mod tidy
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/pgweb .

FROM alpine:3.22.5@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce

RUN apk add --no-cache \
        ca-certificates=20260611-r0 \
        curl=8.14.1-r3 \
        netcat-openbsd=1.229.1-r0 \
        postgresql17-client=17.10-r0 && \
    adduser -D -H -s /sbin/nologin pgweb
COPY --from=build /out/pgweb /usr/bin/pgweb

USER pgweb
EXPOSE 8081
ENTRYPOINT ["/usr/bin/pgweb", "--bind=0.0.0.0", "--listen=8081"]
