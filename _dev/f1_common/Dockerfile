FROM python:3.12-slim

WORKDIR /app
COPY app/ /app/

COPY gateway_server.py /opt/pulsewire-gateway/gateway_server.py
COPY start.sh /opt/pulsewire-gateway/start.sh
RUN chmod +x /opt/pulsewire-gateway/start.sh

ENV GATEWAY_URL=http://127.0.0.1:8765
ENV GATEWAY_DATA_DIR=/data
RUN mkdir -p /data

ENTRYPOINT ["/opt/pulsewire-gateway/start.sh"]
