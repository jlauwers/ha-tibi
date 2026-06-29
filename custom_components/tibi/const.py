"""Constants for the TIBI integration."""

DOMAIN = "tibi"

# Config entries
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 3600  # 1 heure

# URLs confirmées via DevTools
BASE_URL   = "https://tibi.monconteneur.be"
LOGIN_URL  = f"{BASE_URL}/login"
HOME_URL   = f"{BASE_URL}/home"
# API JSON : GET /app.php?page=history&year=YYYY  (XHR, retourne du JSON)
API_URL    = f"{BASE_URL}/app.php"

# Noms des fractions (tels qu'affichés / retournés par l'API)
FRACTION_TOUT_VENANT = "TOUT VENANT"
FRACTION_ORGANIQUE   = "ORGANIQUE"

# Unités
UNIT_KG          = "kg"
UNIT_COLLECTIONS = "vidanges"

# Attributs extra des sensors
ATTR_LAST_DATE  = "derniere_levee"
ATTR_LAST_KG    = "derniere_levee_kg"
ATTR_STATUS     = "statut"
ATTR_NR_PUCE    = "nr_puce"
ATTR_HOUSEHOLD  = "composition_menage"
ATTR_ADDRESS    = "adresse"
ATTR_YEAR       = "annee"
