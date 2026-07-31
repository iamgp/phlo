FROM golang:1.26.5-alpine3.23@sha256:622e56dbc11a8cfe87cafa2331e9a201877271cbff918af53d3be315f3da88cc AS build

RUN apk add --no-cache git=2.52.0-r0
WORKDIR /src
RUN git clone https://github.com/airlift/launcher.git . && \
    git checkout e0e239b162b4dd45f60aacd5c58394d2832d0d13
WORKDIR /src/src/main/go
RUN go get golang.org/x/text@v0.39.0 && \
    CGO_ENABLED=0 go build -buildvcs=false -trimpath \
      -ldflags="-s -w -extldflags=-static -X launcher/args.Version=318" \
      -o /out/launcher .

FROM trinodb/trino:483@sha256:db58cc93e593a2706553745f276bb119c9810e69918be56ecde088ba7ccb0534

ARG TARGETARCH
COPY --from=build --chown=trino:trino /out/launcher /usr/lib/trino/bin/linux-${TARGETARCH}/launcher

USER trino
