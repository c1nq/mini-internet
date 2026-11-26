#!/usr/bin/env bash
# Laat zien of transit verbonden is met Routinator en welke netwerken hij
# als geldig herkent. Herstelt de verbinding eerst automatisch, voor het
# geval de eerste verbindingspoging bij het opstarten te vroeg kwam.
sudo docker exec clab-mini-internet-transit vtysh -c "rpki reset" >/dev/null 2>&1
sleep 3
sudo docker exec clab-mini-internet-transit vtysh -c "show rpki cache-connection"
echo
sudo docker exec clab-mini-internet-transit vtysh -c "show rpki prefix-table"
