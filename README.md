# Mini internet

![Mini internet](docs/banner.png)

Ik bouw op mijn laptop een klein internet na om te snappen hoe BGP werkt en hoe je het kunt aanvallen en beveiligen. BGP is het protocol waarmee grote netwerken op internet aan elkaar vertellen welke IP adressen bij hen zitten. Standaard wordt dat vooral op vertrouwen aangenomen, en dat wil ik zelf zien misgaan.

Alles draait lokaal in containers met private IP adressen en AS nummers. Het is niet verbonden met echte routers.

## Opbouw nu

| Router | AS | Netwerk |
|---|---|---|
| transit | 65001 | 10.1.0.0/24 |
| bank | 65002 | 10.2.0.0/24 |
| aanvaller | 65003 | 10.3.0.0/24 |
| klant | 65004 | 10.4.0.0/24 |

De bank, de aanvaller en de klant zijn alleen met transit verbonden.

## Nodig

Linux (Ubuntu VM of WSL2), Docker en [Containerlab](https://containerlab.dev).

## Starten

```bash
sudo containerlab deploy -t topology.clab.yml
```

Kijken of de BGP sessies werken:

```bash
docker exec -it clab-mini-internet-transit vtysh -c "show bgp summary"
```

Testen of de aanvaller de bank kan bereiken:

```bash
docker exec -it clab-mini-internet-aanvaller ping -c 3 -I 10.3.0.1 10.2.0.1
```

Stoppen:

```bash
sudo containerlab destroy -t topology.clab.yml
```

De regel `no bgp ebgp-requires-policy` staat er nu in zodat routes zonder filter worden uitgewisseld. Bij de beveiliging ga ik dat aanpassen.

## Planning

- [x] Drie routers die elkaar bereiken
- [x] Website voor de bank
- [ ] DNS
- [x] Route kapen
- [ ] Filters en RPKI
- [ ] Live kaart in de browser

## Eerste kaping

De bank kondigt 10.2.0.0/24 aan. Ik heb de aanvaller 10.2.0.0/25 laten aankondigen. Omdat een router altijd de meest specifieke route kiest, ging het verkeer voor 10.2.0.1 daarna naar de aanvaller, terwijl er bij de bank niks veranderd was.

| Situatie | Route op transit | Gaat naar |
|---|---|---|
| Normaal | 10.2.0.0/24 via 10.255.12.2 | bank |
| Gekaapt | 10.2.0.0/25 via 10.255.13.2 | aanvaller |
| Met filter | 10.2.0.0/24 via 10.255.12.2 | bank |

Daarna heb ik op transit een filter gezet zodat de aanvaller alleen zijn eigen netwerk mag aankondigen:

```
ip prefix-list AANVALLER-IN seq 5 permit 10.3.0.0/24
router bgp 65001
 address-family ipv4 unicast
  neighbor 10.255.13.2 prefix-list AANVALLER-IN in
```

Het duurde even voordat de route terug was. Eerst dacht ik dat het filter niet werkte, maar bij de tweede controle klopte het wel.

## Website kapen

Bij de bank en de aanvaller draait nu een webserver. De klant vraagt steeds hetzelfde adres op, http://10.2.0.1.

```bash
sudo bash scripts/bezoek.sh   # Echte bank
sudo bash scripts/kaping.sh
sudo bash scripts/bezoek.sh   # GEKAAPT
sudo bash scripts/filter.sh
sudo bash scripts/bezoek.sh   # Echte bank
```

Wacht na het kapen en filteren een paar seconden, de routes zijn niet meteen aangepast. De klant merkt zelf niks, die gebruikt gewoon hetzelfde adres.
