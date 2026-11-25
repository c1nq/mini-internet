#!/bin/sh
grep -q bank.lab /etc/hosts || echo "10.2.0.1 bank.lab" >> /etc/hosts
