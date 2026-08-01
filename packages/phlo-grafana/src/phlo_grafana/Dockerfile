FROM golang:1.26.5-alpine3.23@sha256:622e56dbc11a8cfe87cafa2331e9a201877271cbff918af53d3be315f3da88cc AS build

RUN apk add --no-cache git=2.52.0-r0

WORKDIR /src/grafana
RUN git clone https://github.com/grafana/grafana.git . && \
    git checkout a9cee6e1724a455676bb6c05eef7fc54aa4b19f4
RUN go get \
      github.com/getkin/kin-openapi@v0.144.0 \
      github.com/grafana/tempo@8100f5a7b8f0986edf1fcd2ff6552d174b25ec18 \
      google.golang.org/grpc@v1.82.1 \
      golang.org/x/text@v0.39.0 && \
    CGO_ENABLED=0 go build -buildvcs=false -trimpath \
      -ldflags="-s -w -X main.version=13.1.1 -X main.commit=a9cee6e1724a455676bb6c05eef7fc54aa4b19f4" \
      -o /out/grafana ./pkg/cmd/grafana

WORKDIR /src/elasticsearch
RUN git clone https://github.com/grafana/grafana-elasticsearch-datasource.git . && \
    git checkout 525671446900cf0c7c5d696f931b95c2cec81d9c && \
    go get google.golang.org/grpc@v1.82.1 golang.org/x/text@v0.39.0 && \
    CGO_ENABLED=0 go build -buildvcs=false -trimpath -ldflags="-s -w" \
      -o /out/elasticsearch ./pkg

WORKDIR /src/zipkin
RUN git clone https://github.com/grafana/grafana-zipkin-datasource.git . && \
    git checkout daafdfe11421dd2cacc8bfdb9ab604da1875b671 && \
    go get golang.org/x/net@v0.55.0 golang.org/x/text@v0.39.0 google.golang.org/grpc@v1.82.1 && \
    CGO_ENABLED=0 go build -buildvcs=false -trimpath -ldflags="-s -w" \
      -o /out/zipkin ./pkg

FROM grafana/grafana:13.1.1@sha256:7cb8c64c4d57a57e734073f3cc94620adb24a0acb929bd80ba9f14017e3a975b

ARG TARGETARCH
COPY --from=build /out/grafana /usr/share/grafana/bin/grafana
COPY --from=build /out/elasticsearch /usr/share/grafana/data/plugins-bundled/elasticsearch/gpx_grafana_elasticsearch_datasource_linux_${TARGETARCH}
COPY --from=build /out/zipkin /usr/share/grafana/data/plugins-bundled/zipkin/gpx_grafana-zipkin-datasource_linux_${TARGETARCH}

USER "472"
