FROM python:3.12-slim

# 安装 docker CLI（用于操作宿主机容器）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-27.5.1.tgz \
    | tar xz --strip-components=1 -C /usr/local/bin docker/docker \
    && apt-get remove -y curl && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# 安装 docker compose plugin
RUN mkdir -p /usr/local/lib/docker/cli-plugins \
    && apt-get update && apt-get install -y --no-install-recommends curl \
    && curl -fsSL "https://github.com/docker/compose/releases/download/v2.33.1/docker-compose-linux-x86_64" \
       -o /usr/local/lib/docker/cli-plugins/docker-compose \
    && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
    && apt-get remove -y curl && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/travel-ai

EXPOSE 9090

CMD ["python", "deploy/ai-ops/server.py"]
