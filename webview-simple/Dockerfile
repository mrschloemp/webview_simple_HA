FROM ghcr.io/home-assistant/amd64-base:latest

RUN apk add --no-cache python3 py3-pip && \
    pip3 install --no-cache-dir --break-system-packages \
    aiohttp beautifulsoup4 lxml

COPY rootfs /
RUN chmod +x /usr/bin/proxy.py
CMD ["python3", "/usr/bin/proxy.py"]
