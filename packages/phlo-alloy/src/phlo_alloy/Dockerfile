FROM grafana/alloy-build-image:v0.1.34@sha256:4371598809230ffd7611367ba0dcb92bbc8b74bda88471293e5d478b48a0d186 AS build

RUN git clone https://github.com/grafana/alloy.git /src/alloy && \
    git -C /src/alloy checkout a435563ff073d5355952c1a8d1821110b1392691
WORKDIR /src/alloy
RUN go get google.golang.org/grpc@v1.82.1 && \
    go mod tidy
WORKDIR /src/alloy/internal/web/ui
RUN npm ci --no-audit --no-fund && npm run build
WORKDIR /src/alloy
# hadolint ignore=DL3062
RUN RELEASE_BUILD=1 \
    VERSION=v1.18.0 \
    GO_TAGS="netgo embedalloyui promtail_journal_enabled" \
    SKIP_UI_BUILD=1 \
    make alloy

FROM grafana/alloy:v1.18.0@sha256:491b0578c04983fd54fe99b587b6fab4404dc46d0dc16677bd6b00cc1140b308

COPY --from=build /src/alloy/build/alloy /bin/alloy
