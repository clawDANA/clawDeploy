# syntax=docker/dockerfile:1

# ── Stage 1: Build ────────────────────────────────────────────
FROM alpine:3.21 AS builder

RUN apk add --no-cache sqlite-dev musl-dev git wget xz

RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then ZIG_ARCH="x86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then ZIG_ARCH="aarch64"; \
    else ZIG_ARCH="$ARCH"; fi && \
    wget -q https://ziglang.org/download/0.15.2/zig-${ZIG_ARCH}-linux-0.15.2.tar.xz && \
    tar -xf zig-${ZIG_ARCH}-linux-0.15.2.tar.xz && \
    mv zig-${ZIG_ARCH}-linux-0.15.2 /usr/local/zig && \
    ln -s /usr/local/zig/zig /usr/local/bin/zig && \
    rm zig-${ZIG_ARCH}-linux-0.15.2.tar.xz

WORKDIR /app
COPY nullclaw/ .

RUN zig build -Doptimize=ReleaseSmall

# ── Stage 2: Config Prep ─────────────────────────────────────
FROM busybox:1.37 AS permissions

RUN mkdir -p /nullclaw-data/.nullclaw /nullclaw-data/workspace /scripts

RUN cat > /scripts/entrypoint.sh << 'EOF'
#!/bin/sh
cat > /nullclaw-data/.nullclaw/config.json <<CONFIG
{
  "default_provider": "openrouter",
  "default_model": "${NULLCLAW_MODEL:-liquid/lfm-2.5-1.2b-instruct:free}",
  "models": {
    "providers": {
      "openrouter": {
        "api_key": "${NULLCLAW_API_KEY}"
      }
    }
  },
  "channels": {
    "telegram": {
      "accounts": {
        "main": {
          "bot_token": "${TELEGRAM_BOT_TOKEN}",
          "allow_from": ["*"],
          "reply_in_private": true
        }
      }
    }
  },
  "gateway": {
    "port": 3000,
    "host": "0.0.0.0",
    "require_pairing": false,
    "allow_public_bind": true
  },
  "autonomy": {
    "level": "supervised",
    "workspace_only": true
  }
}
CONFIG
exec /usr/local/bin/nullclaw "$@"
EOF

RUN chmod +x /scripts/entrypoint.sh
RUN chown -R 65534:65534 /nullclaw-data /scripts

# ── Stage 3: Production Runtime (Alpine) ─────────────────
FROM alpine:3.21 AS release

COPY --from=builder /app/zig-out/bin/nullclaw /usr/local/bin/nullclaw
COPY --from=permissions /nullclaw-data /nullclaw-data
COPY --from=permissions /scripts /scripts

ENV NULLCLAW_WORKSPACE=/nullclaw-data/workspace
ENV HOME=/nullclaw-data
ENV NULLCLAW_GATEWAY_PORT=3000

WORKDIR /nullclaw-data
USER 65534:65534
EXPOSE 3000
ENTRYPOINT ["/scripts/entrypoint.sh"]
CMD ["daemon"]
