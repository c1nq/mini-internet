#!/usr/bin/env bash
docker exec clab-mini-internet-aanvaller vtysh -c "conf t" -c "router bgp 65003" -c "address-family ipv4 unicast" -c "no network 10.2.0.0/25" -c "exit" -c "exit" -c "interface lo" -c "no ip address 10.2.0.1/25"
