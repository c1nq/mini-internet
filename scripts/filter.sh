#!/usr/bin/env bash
docker exec clab-mini-internet-transit vtysh -c "conf t" -c "ip prefix-list AANVALLER-IN seq 5 permit 10.3.0.0/24" -c "router bgp 65001" -c "address-family ipv4 unicast" -c "neighbor 10.255.13.2 prefix-list AANVALLER-IN in"
docker exec clab-mini-internet-transit vtysh -c "clear bgp ipv4 unicast 10.255.13.2 soft in"
