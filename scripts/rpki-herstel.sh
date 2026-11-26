#!/usr/bin/env bash
# Dwingt transit om opnieuw verbinding te maken met Routinator. Nodig omdat
# bgpd's eerste verbindingspoging bij het opstarten te vroeg komt, voordat
# Routinator klaar is. Wordt automatisch aangeroepen na elke deploy.
sudo docker exec clab-mini-internet-transit vtysh -c "rpki reset" >/dev/null
sleep 3
sudo docker exec clab-mini-internet-transit vtysh -c "show rpki cache-connection"
