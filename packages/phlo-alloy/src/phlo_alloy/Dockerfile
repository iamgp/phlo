FROM grafana/alloy-build-image:v0.1.34@sha256:4371598809230ffd7611367ba0dcb92bbc8b74bda88471293e5d478b48a0d186 AS build

RUN git init /src/alloy && \
    git -C /src/alloy remote add origin https://github.com/grafana/alloy.git && \
    git -C /src/alloy fetch --depth 1 origin a435563ff073d5355952c1a8d1821110b1392691 && \
    git -C /src/alloy checkout --detach FETCH_HEAD && \
    rm -rf /src/alloy/.git
WORKDIR /src/alloy
# hadolint ignore=DL3062
RUN export GOCACHE=/tmp/go-cache GOMODCACHE=/tmp/go-mod && \
    go get \
        google.golang.org/grpc@v1.82.1 \
        github.com/docker/docker@v29.3.1+incompatible \
        github.com/go-git/go-git/v5@v5.19.2 \
        golang.org/x/text@v0.39.0 && \
    go mod tidy && \
    npm --prefix internal/web/ui ci --no-audit --no-fund && \
    npm --prefix internal/web/ui run build && \
    RELEASE_BUILD=1 \
        VERSION=v1.18.0 \
        GO_TAGS="netgo embedalloyui promtail_journal_enabled" \
        SKIP_UI_BUILD=1 \
        make alloy && \
    rm -rf internal/web/ui/node_modules /tmp/go-cache /tmp/go-mod

FROM grafana/alloy:v1.18.0@sha256:491b0578c04983fd54fe99b587b6fab4404dc46d0dc16677bd6b00cc1140b308

COPY --from=build /src/alloy/build/alloy /bin/alloy

USER "473"
