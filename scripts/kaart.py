#!/usr/bin/env python3
"""Live kaart van het mini internet. Starten: python3 scripts/kaart.py"""
import json
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

POORT = 8000
LAB = "clab-mini-internet-"


def docker(node, *args):
    try:
        r = subprocess.run(["docker", "exec", LAB + node, *args],
                           capture_output=True, text=True, timeout=10)
        return r.stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def vtysh(node, *regels):
    args = ["vtysh"]
    for regel in regels:
        args += ["-c", regel]
    return docker(node, *args)


def kaping():
    vtysh("aanvaller", "conf t", "interface lo", "ip address 10.2.0.1/25", "exit",
          "router bgp 65003", "address-family ipv4 unicast", "network 10.2.0.0/25")


def filteren():
    vtysh("transit", "conf t", "ip prefix-list AANVALLER-IN seq 5 permit 10.3.0.0/24",
          "router bgp 65001", "address-family ipv4 unicast",
          "neighbor 10.255.13.2 prefix-list AANVALLER-IN in")
    vtysh("transit", "clear bgp ipv4 unicast 10.255.13.2 soft in")


def herstel():
    vtysh("aanvaller", "conf t", "router bgp 65003", "address-family ipv4 unicast",
          "no network 10.2.0.0/25")
    vtysh("aanvaller", "conf t", "interface lo", "no ip address 10.2.0.1/25")
    vtysh("transit", "conf t", "router bgp 65001", "address-family ipv4 unicast",
          "no neighbor 10.255.13.2 prefix-list AANVALLER-IN in")
    vtysh("transit", "conf t", "no ip prefix-list AANVALLER-IN")
    vtysh("transit", "clear bgp ipv4 unicast 10.255.13.2 soft in")


def status():
    uit = {"prefix": None, "doel": None, "filter": False, "pagina": ""}
    try:
        routes = json.loads(vtysh("transit", "show ip route 10.2.0.1 json"))
        for prefix, lijst in routes.items():
            ip = lijst[0]["nexthops"][0].get("ip")
            uit["prefix"] = prefix
            uit["doel"] = {"10.255.12.2": "bank", "10.255.13.2": "aanvaller"}.get(ip)
    except (ValueError, KeyError, IndexError, AttributeError):
        pass
    uit["filter"] = "AANVALLER-IN in" in vtysh("transit", "show running-config")
    uit["pagina"] = docker("klant", "wget", "-qO-", "-T", "3", "http://10.2.0.1")
    return uit


PAGINA = """<!doctype html>
<html lang="nl"><head><meta charset="utf-8"><title>mini internet</title>
<style>
body{margin:0;background:#0d1117;color:#e6edf3;font-family:system-ui,sans-serif}
main{max-width:900px;margin:0 auto;padding:24px}
svg{width:100%;height:auto}
line{stroke:#30363d;stroke-width:3}
line.pad{stroke:#fff;stroke-dasharray:10 10;animation:loop 1s linear infinite}
line.fout{stroke:#f85149}
@keyframes loop{to{stroke-dashoffset:-20}}
circle{fill:#0d1117;stroke:#fff;stroke-width:3}
circle.rood{fill:#f85149;stroke:#f85149}
text{fill:#e6edf3;font-size:17px;text-anchor:middle}
text.klein{fill:#8b949e;font-size:13px}
button{background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:10px 20px;margin-right:8px;font-size:15px;cursor:pointer}
button:disabled{opacity:.4}
.kaart{border:1px solid #30363d;border-radius:6px;padding:12px 16px;margin-top:16px}
.browser{background:#fff;color:#111}
.browser small{color:#666}
</style></head><body><main>
<h1>mini internet</h1>
<svg viewBox="0 0 800 400">
<line id="klant" x1="110" y1="200" x2="400" y2="200"/>
<line id="bank" x1="400" y1="200" x2="680" y2="90"/>
<line id="aanvaller" x1="400" y1="200" x2="680" y2="310"/>
<circle cx="110" cy="200" r="24"/><text x="110" y="250">klant</text><text class="klein" x="110" y="270">AS 65004</text>
<circle cx="400" cy="200" r="30"/><text x="400" y="255">transit</text><text class="klein" x="400" y="275">AS 65001</text>
<circle cx="680" cy="90" r="24"/><text x="680" y="40">bank</text><text class="klein" x="680" y="58">AS 65002</text>
<circle class="rood" cx="680" cy="310" r="24"/><text x="680" y="360">aanvaller</text><text class="klein" x="680" y="380">AS 65003</text>
</svg>
<button data-a="kaping">Kapen</button><button data-a="filter">Filter aan</button><button data-a="herstel">Herstellen</button>
<div class="kaart" id="info">Laden...</div>
<div class="kaart browser"><small>Wat de klant ziet op http://10.2.0.1</small><iframe id="site" sandbox style="width:100%;height:130px;border:0"></iframe></div>
</main><script>
const el = id => document.getElementById(id);
let vorige = null;
async function ververs(){
  try{
    const s = await (await fetch('/status')).json();
    for (const id of ['klant','bank','aanvaller']){
      const aan = s.doel && (id === 'klant' || id === s.doel);
      el(id).setAttribute('class', aan ? 'pad' + (s.doel === 'aanvaller' ? ' fout' : '') : '');
    }
    el('info').textContent = s.doel
      ? 'Route op transit: ' + s.prefix + ' naar ' + s.doel + '. Filter: ' + (s.filter ? 'aan' : 'uit')
      : 'Geen route gevonden. Draait het lab?';
    if (s.pagina !== vorige){ vorige = s.pagina; el('site').srcdoc = s.pagina || 'Geen antwoord'; }
  }catch(e){ el('info').textContent = 'Geen verbinding met kaart.py'; }
}
for (const b of document.querySelectorAll('button')){
  b.onclick = async () => {
    b.disabled = true;
    await fetch('/' + b.dataset.a, {method:'POST', headers:{'X-Lab':'1'}});
    b.disabled = false;
    ververs();
  };
}
(async function lus(){ await ververs(); setTimeout(lus, 2000); })();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def stuur(self, code, soort, inhoud):
        data = inhoud.encode()
        self.send_response(code)
        self.send_header("Content-Type", soort + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def lokaal(self):
        # alleen verzoeken aan localhost, tegen DNS rebinding
        return self.headers.get("Host") in (f"localhost:{POORT}", f"127.0.0.1:{POORT}")

    def do_GET(self):
        if not self.lokaal():
            return self.stuur(403, "text/plain", "geweigerd")
        if self.path == "/":
            return self.stuur(200, "text/html", PAGINA)
        if self.path == "/status":
            return self.stuur(200, "application/json", json.dumps(status()))
        self.stuur(404, "text/plain", "niet gevonden")

    def do_POST(self):
        # de eigen header voorkomt dat een andere website de knoppen kan bedienen
        if not self.lokaal() or self.headers.get("X-Lab") != "1":
            return self.stuur(403, "text/plain", "geweigerd")
        actie = {"/kaping": kaping, "/filter": filteren, "/herstel": herstel}.get(self.path)
        if not actie:
            return self.stuur(404, "text/plain", "niet gevonden")
        actie()
        self.stuur(200, "text/plain", "ok")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Kaart staat op http://localhost:{POORT}  (stoppen met Ctrl+C)")
    ThreadingHTTPServer(("127.0.0.1", POORT), Handler).serve_forever()
