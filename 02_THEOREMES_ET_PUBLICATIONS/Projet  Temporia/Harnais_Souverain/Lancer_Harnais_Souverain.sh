#!/usr/bin/env bash
# ==============================================================================
#           ⚡ DÉMARRAGE DU HARNAIS D'AGENTIVITÉ SOUVERAIN (LINUX / MAC) ⚡
# ==============================================================================

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python 3 n'est pas installé."
    exit 1
fi

python3 run_harness.py --profile default
