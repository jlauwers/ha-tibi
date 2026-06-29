# TIBI Quotas Conteneurs — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/jlauwers/ha-tibi.svg)](https://github.com/jlauwers/ha-tibi/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Intégration Home Assistant pour suivre vos **quotas de collecte TIBI** (conteneurs à puce, intercommunale de Thuin-Binche, Wallonie).

Récupère automatiquement vos données depuis [tibi.monconteneur.be](https://tibi.monconteneur.be) et expose des sensors dans Home Assistant.

---

## Sensors créés

| Entité | Description | Unité |
|--------|-------------|-------|
| `sensor.tibi_tout_venant_levees` | Nombre de levées Tout Venant (année en cours) | vidanges |
| `sensor.tibi_tout_venant_kilos` | Poids collecté Tout Venant (année en cours) | kg |
| `sensor.tibi_organique_levees` | Nombre de levées Organique/GFT (année en cours) | vidanges |
| `sensor.tibi_organique_kilos` | Poids collecté Organique/GFT (année en cours) | kg |

### Attributs disponibles sur chaque sensor

| Attribut | Description |
|----------|-------------|
| `nr_puce` | Numéro de puce du conteneur |
| `statut` | État du conteneur (`active` / `inactive`) |
| `depuis` | Date d'activation de la puce |
| `derniere_levee` | Date de la dernière collecte (`YYYY-MM-DD`) |
| `derniere_levee_kg` | Poids de la dernière collecte |
| `collectes` | Liste de toutes les collectes de l'année |
| `composition_menage` | Nombre de personnes dans le ménage |
| `adresse` | Adresse enregistrée |
| `annee` | Année des données |
| `actif_depuis` | Date d'activation du titulaire |

---

## Installation via HACS (recommandée)

1. Dans Home Assistant, ouvre **HACS** → **Intégrations**
2. Clique sur le menu ⋮ → **Dépôts personnalisés**
3. Ajoute l'URL : `https://github.com/jlauwers/ha-tibi`  
   Catégorie : **Intégration**
4. Cherche **"TIBI"** dans HACS et clique **Télécharger**
5. Redémarre Home Assistant

### Installation manuelle

```bash
# Via SSH sur ton serveur HA
cp -r custom_components/tibi /config/custom_components/
```

Redémarre Home Assistant.

---

## Configuration

Paramètres → Appareils & Services → **+ Ajouter une intégration** → cherche **TIBI**

Saisis tes identifiants du portail [tibi.monconteneur.be](https://tibi.monconteneur.be).

---

## Exemple de carte Lovelace

```yaml
type: entities
title: 🗑️ TIBI – Mes conteneurs 2026
entities:
  - entity: sensor.tibi_tout_venant_levees
    name: Tout Venant – Levées
    icon: mdi:trash-can-outline
  - entity: sensor.tibi_tout_venant_kilos
    name: Tout Venant – Kilos
    icon: mdi:weight-kilogram
  - entity: sensor.tibi_organique_levees
    name: Organique – Levées
    icon: mdi:leaf
  - entity: sensor.tibi_organique_kilos
    name: Organique – Kilos
    icon: mdi:weight-kilogram
```

### Avec historique (carte Statistics Graph)

```yaml
type: statistics-graph
title: TIBI – Évolution du poids
entities:
  - sensor.tibi_tout_venant_kilos
  - sensor.tibi_organique_kilos
period:
  calendar:
    period: month
stat_types:
  - max
```

---

## Compatibilité

- **Intercommunale** : TIBI (Thuin-Binche, Wallonie, Belgique)
- **Portail** : [tibi.monconteneur.be](https://tibi.monconteneur.be) (plateforme CI-WEB)
- **Fractions supportées** : Tout Venant (REST) · Organique/GFT
- **Home Assistant** : 2024.1.0+
- **Mise à jour** : toutes les heures (configurable, min 5 min)

> Cette intégration utilise une session PHP standard (form POST + cookie `PHPSESSID`).
> Aucune API officielle publique n'est disponible.

---

## Debugging

Active les logs détaillés dans `configuration.yaml` :

```yaml
logger:
  default: warning
  logs:
    custom_components.tibi: debug
```

---

## Contribution

Issues et PR bienvenus ! Pour contribuer :

1. Fork → branche feature
2. `pip install -r requirements_dev.txt`
3. PR vers `main`

---

## Licence

MIT — voir [LICENSE](LICENSE)
