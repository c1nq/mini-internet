#!/usr/bin/env bash
# Vraagt bij de eigen CA een ECHT geldig certificaat voor bank.lab aan,
# via ACME (hetzelfde protocol als Let's Encrypt gebruikt).
# Gebruik: sudo bash scripts/vraag-certificaat.sh bank
#      of: sudo bash scripts/vraag-certificaat.sh aanvaller
set -euo pipefail
NAAM="${1:?geef bank of aanvaller op}"
CONTAINER="clab-mini-internet-web-$NAAM"
ROUTER="clab-mini-internet-$NAAM"

# De CA zoekt bank.lab zelf op om de ACME uitdaging te controleren.
docker exec -u root clab-mini-internet-ca sh -c 'grep -q bank.lab /etc/hosts || echo "10.2.0.1 bank.lab" >> /etc/hosts'

docker exec "$CONTAINER" sh -c '
  set -e
  apk add --no-cache curl openssl bash >/dev/null 2>&1
  [ -f /root/.acme.sh/acme.sh ] || curl -s https://get.acme.sh | sh -s email=test@bank.lab >/dev/null
  export PATH=/root/.acme.sh:$PATH
  grep -q bank.lab /etc/hosts || echo "10.2.0.1 bank.lab" >> /etc/hosts
  CA_FP=$(cat /dev/null)
  acme.sh --set-default-ca --server https://10.4.0.1:9000/acme/acme/directory --insecure 2>&1 | tail -3
  acme.sh --issue -d bank.lab -w /usr/share/nginx/html --server https://10.4.0.1:9000/acme/acme/directory --insecure --force
'
echo
echo "Resultaat: dit container (web-$NAAM) heeft nu een geldig certificaat voor bank.lab."
echo "Bekijk het met:"
echo "  docker exec $CONTAINER sh -c 'openssl x509 -in /root/.acme.sh/bank.lab_ecc/bank.lab.cer -noout -subject -issuer'"
