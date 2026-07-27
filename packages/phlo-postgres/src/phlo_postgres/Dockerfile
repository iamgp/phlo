FROM golang:1.26.5-alpine3.24@sha256:0178a641fbb4858c5f1b48e34bdaabe0350a330a1b1149aabd498d0699ff5fb2 AS gosu-build

RUN apk add --no-cache git=2.54.0-r0
WORKDIR /src
RUN git clone https://github.com/tianon/gosu.git . && \
    git checkout 6456aaa0f3c854d199d0f037f068eb97515b7513
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/gosu .

FROM postgres:18.4-alpine3.24@sha256:9a8afca54e7861fd90fab5fdf4c42477a6b1cb7d293595148e674e0a3181de15

RUN apk upgrade --no-cache
COPY --from=gosu-build /out/gosu /usr/local/bin/gosu

USER postgres
