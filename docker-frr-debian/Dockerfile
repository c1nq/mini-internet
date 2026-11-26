FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates gnupg lsb-release iproute2 && \
    curl -s https://deb.frrouting.org/frr/keys.gpg -o /usr/share/keyrings/frrouting.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/frrouting.gpg] https://deb.frrouting.org/frr $(lsb_release -s -c) frr-stable" \
      > /etc/apt/sources.list.d/frr.list && \
    apt-get update && apt-get install -y --no-install-recommends \
      frr frr-pythontools frr-rpki-rtrlib && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/run/frr && chown frr:frr /var/run/frr /etc/frr

COPY docker-start /usr/lib/frr/docker-start
RUN chmod 0755 /usr/lib/frr/docker-start

CMD ["/usr/lib/frr/docker-start"]
