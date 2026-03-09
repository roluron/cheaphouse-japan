# PROMPT À COLLER DANS ANTIGRAVITY — Fix TOUT ce qui marche pas (bugs + cron + auto)

```
Auto-approve all changes and commands. Don't ask for permission.

## URGENCE — 3 problèmes à régler MAINTENANT

Le pipeline tourne mais il y a 3 trucs cassés. Fixe TOUT sans demander.

---

## FIX 1: bukkenfan adapter — crash sur les prix japonais

L'erreur: `invalid literal for int() with base 10: '9280万円'`

Le problème: l'adapter bukkenfan fait `int(price_text)` direct au lieu d'utiliser le parser japonais.

### Ce qu'il faut faire:

1. Ouvre `ingestion/adapters/bukkenfan_jp.py`
2. Cherche TOUT endroit où un prix est parsé avec `int()` ou `float()` directement
3. Remplace par `parse_japanese_price()` depuis utils

```python
# AVANT (cassé):
price_jpy = int(price_text)

# APRÈS (correct):
from ingestion.utils import parse_japanese_price

def safe_parse_price(text):
    """Parse price: try Japanese format first, then plain number."""
    price = parse_japanese_price(text)
    if price is not None:
        return price
    # Fallback: plain number
    try:
        cleaned = text.replace(',', '').replace('円', '').replace('¥', '').strip()
        return int(cleaned) if cleaned.isdigit() else None
    except (ValueError, AttributeError):
        return None

price_jpy = safe_parse_price(price_text)
```

4. Vérifie aussi TOUS les autres adapters — si un adapter fait `int()` sur du texte de prix, fixe-le pareil
5. Si `parse_japanese_price` n'existe pas dans utils.py, crée-le:

```python
def parse_japanese_price(text: str) -> int | None:
    """
    Parse Japanese price text to integer yen.
    Handles: '9280万円', '980万', '1億2000万円', '5,000,000円', '500万円〜'
    """
    import re
    if not text:
        return None

    text = text.strip().replace(',', '').replace('円', '').replace('¥', '')
    text = re.sub(r'〜.*', '', text)  # Remove range suffix
    text = re.sub(r'～.*', '', text)

    # Pattern: N億M万
    match = re.match(r'(\d+)億(\d+)万', text)
    if match:
        return int(match.group(1)) * 100_000_000 + int(match.group(2)) * 10_000

    # Pattern: N億
    match = re.match(r'(\d+)億', text)
    if match:
        return int(match.group(1)) * 100_000_000

    # Pattern: N万
    match = re.match(r'(\d+)万', text)
    if match:
        return int(match.group(1)) * 10_000

    # Plain number
    try:
        return int(text) if text.isdigit() else None
    except ValueError:
        return None
```

---

## FIX 2: realestate-co-jp adapter — 0 listings

L'adapter realestate-co-jp ne retourne rien. Debug:

1. Ouvre `ingestion/adapters/realestate_co_jp.py`
2. Le problème est probablement:
   - CSS selectors incorrects (le site a changé)
   - Le site utilise JavaScript pour le rendu (les données ne sont pas dans le HTML statique)
   - Headers manquants

3. Va sur https://realestate.co.jp/en/forsale/listing/ dans un navigateur
4. Inspecte le HTML réel — regarde les classes CSS des cartes de listings
5. Si le site charge les listings via JavaScript/API:
   - Ouvre les DevTools → Network tab
   - Filtre par XHR/Fetch
   - Cherche une requête API qui retourne du JSON avec les listings
   - Utilise cette API directement dans l'adapter

6. Si tu ne trouves pas de solution rapide, ajoute un log d'avertissement et continue:
```python
logger.warning("realestate-co-jp: site may require JS rendering. Skipping for now.")
```

7. On a 8 autres sources qui marchent, c'est pas bloquant.

---

## FIX 3: CRON — pas installé !!!

Le cron n'est PAS installé. Le dashboard montre "No cron jobs installed". C'est pour ça que rien ne tourne automatiquement.

### Installe le cron MAINTENANT:

1. Vérifie que `setup_cron.sh` existe dans `ingestion/`
2. Si oui, lance-le: `bash ingestion/setup_cron.sh`
3. Si non, crée-le et lance-le:

```bash
#!/bin/bash
# setup_cron.sh — Install cron jobs for CheapHouse pipeline
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$SCRIPT_DIR/venv/bin/python"
PIPELINE="$SCRIPT_DIR/auto_pipeline.py"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p "$LOG_DIR"

# Remove old CheapHouse cron entries
crontab -l 2>/dev/null | grep -v "cheaphouse\|auto_pipeline\|CheapHouse" > /tmp/cron_clean

# Add new cron jobs (Mac Mini timezone)
cat >> /tmp/cron_clean << EOF
# CheapHouse Pipeline — Full run at 3:00 AM
0 3 * * * cd "$SCRIPT_DIR" && "$PYTHON" "$PIPELINE" >> "$LOG_DIR/cron_\$(date +\%Y\%m\%d).log" 2>&1

# CheapHouse Pipeline — Freshness check at 2:00 PM
0 14 * * * cd "$SCRIPT_DIR" && "$PYTHON" "$PIPELINE" --freshness >> "$LOG_DIR/cron_fresh_\$(date +\%Y\%m\%d).log" 2>&1
EOF

crontab /tmp/cron_clean
rm /tmp/cron_clean

echo "✅ Cron jobs installed:"
echo ""
crontab -l | grep -i "cheaphouse\|auto_pipeline"
echo ""
echo "Schedule:"
echo "  03:00 — Full pipeline (scrape + enrich + freshness)"
echo "  14:00 — Freshness check only"
```

4. Vérifie que c'est bien installé: `crontab -l`

---

## FIX 4: Ollama auto-start — vérifie

Vérifie aussi que Ollama démarre automatiquement au boot:

```bash
# Check if LaunchAgent exists
ls -la ~/Library/LaunchAgents/com.ollama.plist 2>/dev/null || ls -la ~/Library/LaunchAgents/*ollama* 2>/dev/null

# If not found, Ollama may auto-start from the app. Check:
ls /Applications/Ollama.app 2>/dev/null
```

Si Ollama est installé comme app Mac, il démarre normalement tout seul. Si c'est installé via brew, crée un LaunchAgent:

```bash
cat > ~/Library/LaunchAgents/com.cheaphouse.ollama.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cheaphouse.ollama</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
launchctl load ~/Library/LaunchAgents/com.cheaphouse.ollama.plist
```

---

## Après avoir tout fixé — TEST

```bash
cd "/Users/test/Documents/CheapHouse Japan/ingestion"
source venv/bin/activate

# Test bukkenfan (doit parser '9280万円' correctement)
python run.py scrape --source bukkenfan --limit 3

# Test realestate-co-jp (voir si ça retourne des listings maintenant)
python run.py scrape --source realestate-co-jp --limit 3

# Vérifier cron
crontab -l | grep cheaphouse

# Vérifier Ollama
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print([m['name'] for m in json.load(sys.stdin)['models']])"

echo ""
echo "============================================"
echo "  RÉSULTAT DES FIXES:"
echo "============================================"
echo "  bukkenfan:        $(python run.py scrape --source bukkenfan --limit 1 2>&1 | tail -1)"
echo "  realestate-co-jp: $(python run.py scrape --source realestate-co-jp --limit 1 2>&1 | tail -1)"
echo "  cron:             $(crontab -l 2>/dev/null | grep -c 'auto_pipeline') jobs installés"
echo "  ollama:           $(curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; models=json.load(sys.stdin).get('models',[]); print(f'{len(models)} models loaded')" 2>/dev/null || echo 'NOT RUNNING')"
echo "============================================"
```

Push to GitHub when everything passes.
```
