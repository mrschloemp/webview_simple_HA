FROM ghcr.io/home-assistant/amd64-base-python:3.12

RUN pip3 install --no-cache-dir \
    aiohttp beautifulsoup4 lxml

COPY rootfs /
RUN chmod +x /usr/bin/proxy.py
CMD ["/usr/bin/proxy.py"]
