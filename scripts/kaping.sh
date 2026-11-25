#!/usr/bin/env bash
docker exec clab-mini-internet-aanvaller vtysh -c "conf t" -c "interface lo" -c "ip address 10.2.0.1/25" -c "exit" -c "router bgp 65003" -c "address-family ipv4 unicast" -c "network 10.2.0.0/25"
