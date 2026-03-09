# PROMPT À COLLER DANS ANTIGRAVITY — Installe le CRON MAINTENANT

```
Auto-approve all changes and commands. Don't ask for permission.

## IMPORTANT — LE CRON N'EST PAS INSTALLÉ

On a tout codé mais le cron n'a jamais été installé. `crontab -l` retourne RIEN.
Le setup_cron.sh a un `read -p` interactif qui bloque. On bypass tout ça.

## Étape 1: Installe le cron DIRECTEMENT (pas via setup_cron.sh)

Lance cette commande directement dans le terminal — PAS le script, directement la commande:

```bash
SCRIPT_DIR="/Users/test/Documents/CheapHouse Japan/ingestion"
PYTHON_PATH="$SCRIPT_DIR/venv/bin/python"
PIPELINE="$SCRIPT_DIR/auto_pipeline.py"

# Remove any existing CheapHouse entries
(crontab -l 2>/dev/null | grep -v "auto_pipeline" | grep -v "CheapHouse") > /tmp/cron_clean || true

# Add the cron jobs
cat >> /tmp/cron_clean << CRONEOF

# CheapHouse — Full pipeline: scrape ALL countries + enrich + freshness (daily 3 AM)
0 3 * * * cd "$SCRIPT_DIR" && "$PYTHON_PATH" "$PIPELINE" >> "$SCRIPT_DIR/logs/cron_\$(date +\%Y\%m\%d).log" 2>&1

# CheapHouse — Freshness check only (daily 2 PM)
0 14 * * * cd "$SCRIPT_DIR" && "$PYTHON_PATH" "$PIPELINE" --freshness >> "$SCRIPT_DIR/logs/cron_fresh_\$(date +\%Y\%m\%d).log" 2>&1

# CheapHouse — Enrich only: run LLM enrichment on pending listings (daily 6 AM)
0 6 * * * cd "$SCRIPT_DIR" && "$PYTHON_PATH" "$PIPELINE" --enrich >> "$SCRIPT_DIR/logs/cron_enrich_\$(date +\%Y\%m\%d).log" 2>&1
CRONEOF

# Install
crontab /tmp/cron_clean
rm /tmp/cron_clean

echo "✅ Cron installed. Verifying:"
crontab -l | grep -i "cheaphouse\|auto_pipeline"
```

## Étape 2: Vérifie l'installation

```bash
echo "=== CRON CHECK ==="
echo ""
echo "Installed jobs:"
crontab -l | grep -i "cheaphouse\|auto_pipeline"
echo ""
echo "Count: $(crontab -l | grep -c 'auto_pipeline') jobs"
echo ""
echo "Schedule:"
echo "  03:00 AM — Full pipeline (scrape Japan+Europe+USA+NZ + enrich + freshness)"
echo "  06:00 AM — Enrich only (LLM enrichment for pending listings)"
echo "  02:00 PM — Freshness check (sold/removed detection)"
echo ""

# Verify Python + pipeline exist
SCRIPT_DIR="/Users/test/Documents/CheapHouse Japan/ingestion"
echo "Python exists: $(test -f "$SCRIPT_DIR/venv/bin/python" && echo YES || echo NO)"
echo "Pipeline exists: $(test -f "$SCRIPT_DIR/auto_pipeline.py" && echo YES || echo NO)"
echo ".env exists: $(test -f "$SCRIPT_DIR/.env" && echo YES || echo NO)"
echo ""

# Verify Ollama
echo "Ollama running: $(curl -s http://localhost:11434/api/tags > /dev/null 2>&1 && echo YES || echo NO)"
echo ""

# Verify Mac not sleeping
echo "Sleep disabled: $(pmset -g | grep -c 'disablesleep.*1' 2>/dev/null || echo 'UNKNOWN — run: sudo pmset -a disablesleep 1')"
echo ""
echo "=== DONE ==="
```

## Étape 3: Fix setup_cron.sh pour le futur

Le `read -p` interactif dans setup_cron.sh empêche l'automatisation. Remplace le bloc interactif:

Dans `ingestion/setup_cron.sh`, trouve le bloc:
```bash
    read -p "Replace with new schedule? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing schedule."
        exit 0
    fi
```

Remplace par:
```bash
    echo "Replacing existing schedule automatically."
```

Comme ça le script ne bloque plus jamais.

## Étape 4: Vérifie que le Mac ne se met PAS en veille

```bash
# Disable sleep (requires sudo — try it)
sudo pmset -a disablesleep 1 2>/dev/null || echo "Note: run 'sudo pmset -a disablesleep 1' manually to prevent Mac from sleeping"

# Also set to never sleep on power adapter
sudo pmset -c sleep 0 displaysleep 0 2>/dev/null || true
```

## Étape 5: Test rapide du pipeline

Fais un mini test pour vérifier que tout tourne:

```bash
cd "/Users/test/Documents/CheapHouse Japan/ingestion"
source venv/bin/activate

# Quick test: scrape just 1 listing from koryoya (fastest source)
python auto_pipeline.py --scrape 2>&1 | head -20

echo ""
echo "If you see 'PHASE 1: SCRAPING' above, the pipeline works and cron will run tonight at 3 AM."
```

Push to GitHub.
```
