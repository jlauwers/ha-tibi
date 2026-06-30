# Changelog

## [1.0.2] — 2026-06-30

### Corrigé
- `SensorStateClass.TOTAL` + `last_reset` timezone-aware remplace `TOTAL_INCREASING`
  → plus d'erreurs HA au passage en janvier 2027
- Accumulation correcte de plusieurs conteneurs actifs de même fraction
- `strings.json` ajouté (requis par hassfest / validation HACS)
- `beautifulsoup4` retiré des requirements (inutilisé depuis l'API JSON)
- `debug_json.py` déplacé dans `tools/`

## [1.0.1] — 2026-06-30

### Ajouté
- Icônes `icon.png` (112×112) et `logo.png` (256×256)

## [1.0.0] — 2026-06-29

### Ajouté
- Intégration initiale
- Login automatique sur `tibi.monconteneur.be` (session PHP)
- API JSON `/app.php?page=history&year=YYYY`
- Sensors : levées et kilos pour Tout Venant (REST) et Organique (GFT)
- Attributs : dernière levée, n° puce, statut, composition du ménage, historique annuel
- Configuration via UI (config flow)
- Rafraîchissement configurable (défaut : 1h)
