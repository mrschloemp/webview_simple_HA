ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache python3 py3-pip && \
    pip3 install --no-cache-dir --break-system-packages \
    aiohttp beautifulsoup4 lxml 2>/dev/null || \
    pip3 install --no-cache-dir aiohttp beautifulsoup4 lxml

COPY rootfs /
RUN chmod +x /usr/bin/proxy.py
CMD ["/usr/bin/proxy.py"]
