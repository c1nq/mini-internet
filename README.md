# Mini internet

Ik bouw op mijn laptop een klein internet na om te snappen hoe BGP werkt en hoe je het kunt aanvallen en beveiligen. BGP is het protocol waarmee grote netwerken op internet aan elkaar vertellen welke IP adressen bij hen zitten. Standaard wordt dat vooral op vertrouwen aangenomen, en dat wil ik zelf zien misgaan.

Alles draait lokaal in containers met private IP adressen en AS nummers. Het is niet verbonden met echte routers.

## Opbouw nu

| Router | AS | Netwerk |
|---|---|---|
| transit | 65001 | 10.1.0.0/24 |
| bank | 65002 | 10.2.0.0/24 |
| aanvaller | 65003 | 10.3.0.0/24 |

De bank en de aanvaller zijn allebei alleen met transit verbonden.

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

- [ ] Drie routers die elkaar bereiken
- [ ] DNS en een website voor de bank
- [ ] Route kapen
- [ ] Filters en RPKI
- [ ] Live kaart in de browser
