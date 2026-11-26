#!/usr/bin/env python3
"""
Monitoring en detectie voor BGP route hijacks in het mini internet lab.

Kijkt wat transit daadwerkelijk ontvangt van elke buur, nog voor RPKI of
een route-map het heeft gefilterd, en vergelijkt dat met de baseline uit
configs/routinator/exceptions.json: welk AS nummer welk blok mag
aankondigen, en tot welke maximale prefixlengte. Dit is dezelfde manier
waarop een Security Operations Center of een BGP monitoring dienst als
BGPStream of Cloudflare Radar een kaping detecteert en logt, ook als een
automatische verdediging de kaping zelf al heeft tegengehouden.
"""
import ipaddress
import json
import re
import subprocess
import sys
import time
from datetime import datetime

CONTAINER = "clab-mini-internet-transit"
BUREN = {
    "10.255.12.2": "bank",
    "10.255.13.2": "aanvaller",
    "10.255.14.2": "klant",
}
EXCEPTIONS_PAD = "configs/routinator/exceptions.json"
LOG_PAD = "scripts/monitor-alerts.log"
INTERVAL_SECONDEN = 4

ROOD = "\033[91m"
GROEN = "\033[92m"
GEEL = "\033[93m"
RESET = "\033[0m"

REGEL_PATROON = re.compile(r'^\s*[*>sdhuir=SR]*\s*(\d+\.\d+\.\d+\.\d+/\d+)\s+(.+)$')


def laad_baseline(pad):
    with open(pad, encoding="utf-8") as f:
        data = json.load(f)
    baseline = []
    for item in data["locallyAddedAssertions"]["prefixAssertions"]:
        net = ipaddress.ip_network(item["prefix"])
        baseline.append({
            "net": net,
            "asn": item["asn"],
            "max_lengte": item["maxPrefixLength"],
            "comment": item.get("comment", ""),
        })
    return baseline


def haal_ontvangen_routes(buur_ip):
    try:
        resultaat = subprocess.run(
            ["docker", "exec", CONTAINER, "vtysh", "-c",
             f"show bgp ipv4 unicast neighbors {buur_ip} received-routes"],
            capture_output=True, text=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        return []
    routes = []
    for regel in resultaat.stdout.splitlines():
        m = REGEL_PATROON.match(regel)
        if not m:
            continue
        netwerk_str = m.group(1)
        rest = m.group(2).split()
        if len(rest) >= 2 and rest[-2].isdigit():
            origin_as = int(rest[-2])
            try:
                netwerk = ipaddress.ip_network(netwerk_str)
            except ValueError:
                continue
            routes.append((netwerk, origin_as))
    return routes


def beoordeel(netwerk, origin_as, baseline):
    """Geeft (status, reden) terug. status is 'ok', 'onbekend' of 'afwijkend'."""
    for item in baseline:
        if netwerk.subnet_of(item["net"]) or netwerk == item["net"]:
            if origin_as != item["asn"]:
                return "afwijkend", (
                    f"AS{origin_as} kondigt {netwerk} aan, maar alleen AS{item['asn']} "
                    f"({item['comment']}) is hiervoor geautoriseerd"
                )
            if netwerk.prefixlen > item["max_lengte"]:
                return "afwijkend", (
                    f"AS{origin_as} kondigt {netwerk} aan, een specifiekere prefix dan "
                    f"toegestaan (max /{item['max_lengte']}), typisch voor een route hijack"
                )
            return "ok", None
    return "onbekend", f"AS{origin_as} kondigt {netwerk} aan, een onbekend netwerk"


def log(regel):
    tijdstip = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PAD, "a", encoding="utf-8") as f:
        f.write(f"[{tijdstip}] {regel}\n")


def main():
    baseline = laad_baseline(EXCEPTIONS_PAD)
    print("BGP hijack monitor gestart. Druk op Ctrl+C om te stoppen.")
    print(f"Baseline geladen: {len(baseline)} geautoriseerde netwerken uit {EXCEPTIONS_PAD}")
    print()

    actieve_afwijkingen = set()

    try:
        while True:
            for buur_ip, naam in BUREN.items():
                routes = haal_ontvangen_routes(buur_ip)
                for netwerk, origin_as in routes:
                    status, reden = beoordeel(netwerk, origin_as, baseline)
                    sleutel = (buur_ip, str(netwerk), origin_as)
                    if status != "ok":
                        if sleutel not in actieve_afwijkingen:
                            actieve_afwijkingen.add(sleutel)
                            melding = f"ALERT via buur {naam} ({buur_ip}): {reden}"
                            print(f"{ROOD}{melding}{RESET}")
                            log(melding)
                    else:
                        if sleutel in actieve_afwijkingen:
                            actieve_afwijkingen.discard(sleutel)
                            melding = f"HERSTELD via buur {naam} ({buur_ip}): {netwerk} komt nu overeen met de baseline"
                            print(f"{GROEN}{melding}{RESET}")
                            log(melding)
            time.sleep(INTERVAL_SECONDEN)
    except KeyboardInterrupt:
        print("\nMonitor gestopt.")
        sys.exit(0)


if __name__ == "__main__":
    main()

