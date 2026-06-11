#!/usr/bin/env bash
# fetch_corpus.sh - Recuperation d'un corpus public a licence ouverte pour le TP RAG.
#
# Sources (toutes a licence ouverte / reutilisation autorisee) :
#   - CERT-FR  : avis de securite (HTML + JSON)        -> Licence Ouverte Etalab
#   - CNIL     : guides RGPD (PDF)                      -> reutilisation autorisee
#   - data.gouv: jeux de donnees publics (via API)     -> Licence Ouverte Etalab
#
# Usage :
#   ./fetch_corpus.sh                 # profil par defaut (mixte, ~30 docs)
#   PROFILE=cert   ./fetch_corpus.sh  # projet B : avis CERT-FR
#   PROFILE=cnil   ./fetch_corpus.sh  # projet C : guides CNIL RGPD
#   PROFILE=open   ./fetch_corpus.sh  # projet A : data.gouv + divers
#   N_AVIS=40      ./fetch_corpus.sh  # nombre d'avis CERT-FR a recuperer
#
# Le corpus telecharge va dans corpus/raw/ (gitignore). Le seed reste dans corpus/seed/ (committe).

set -euo pipefail

# --- Repertoires -----------------------------------------------------------
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # racine du projet
RAW_DIR="${HERE}/corpus/raw"
mkdir -p "${RAW_DIR}/cert-fr" "${RAW_DIR}/cnil" "${RAW_DIR}/data-gouv"

PROFILE="${PROFILE:-mixte}"     # mixte | cert | cnil | open
N_AVIS="${N_AVIS:-30}"          # nombre d'avis CERT-FR

# curl robuste : suit les redirections, echoue sur 404, timeout, retries.
CURL=(curl -fSL --retry 3 --retry-delay 2 --connect-timeout 15 -A "tp-rag-formation/1.0")

log()  { printf '\033[0;36m[fetch]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[warn ]\033[0m %s\n' "$*" >&2; }

# --- 1. CERT-FR : avis de securite (HTML + JSON) ---------------------------
# Le flux RSS liste les derniers avis. On en extrait les identifiants
# CERTFR-YYYY-AVI-NNNN, puis on telecharge chaque avis en HTML et en JSON.
fetch_cert() {
  log "CERT-FR : recuperation du flux d'avis..."
  local feed
  feed="$(mktemp)"
  if ! "${CURL[@]}" "https://www.cert.ssi.gouv.fr/avis/feed/" -o "${feed}"; then
    warn "Flux CERT-FR injoignable, on saute cette source."
    return 0
  fi

  # Extraction des IDs d'avis depuis les <link> du flux (grep + sed, ASCII pur).
  local ids
  ids="$(grep -oE 'CERTFR-[0-9]{4}-AVI-[0-9]{4}' "${feed}" | sort -u | head -n "${N_AVIS}")"
  rm -f "${feed}"

  local count=0
  for id in ${ids}; do
    local base="https://www.cert.ssi.gouv.fr/avis/${id}"
    # JSON structure (pratique pour l'analytique du projet B)
    "${CURL[@]}" "${base}/json/" -o "${RAW_DIR}/cert-fr/${id}.json" 2>/dev/null \
      && count=$((count + 1)) \
      || warn "JSON indisponible pour ${id}"
    # Version HTML (pour le challenge d'extraction)
    "${CURL[@]}" "${base}/" -o "${RAW_DIR}/cert-fr/${id}.html" 2>/dev/null \
      || warn "HTML indisponible pour ${id}"
  done
  log "CERT-FR : ${count} avis recuperes dans corpus/raw/cert-fr/"
}

# --- 2. CNIL : guides RGPD (PDF) -------------------------------------------
fetch_cnil() {
  log "CNIL : recuperation des guides RGPD (PDF)..."
  # URLs verifiees HTTP 200 (licence : reutilisation autorisee, mention de la source).
  local urls=(
    "https://www.cnil.fr/sites/default/files/atoms/files/cnil_guide_securite_des_donnees_personnelles-2023.pdf"
    "https://www.cnil.fr/sites/default/files/atoms/files/bpi-cnil-rgpd_guide-tpe-pme.pdf"
    "https://www.cnil.fr/sites/default/files/atoms/files/rgpd-guide_sous-traitant-cnil.pdf"
  )
  local count=0
  for url in "${urls[@]}"; do
    local name
    name="$(basename "${url}")"
    "${CURL[@]}" "${url}" -o "${RAW_DIR}/cnil/${name}" 2>/dev/null \
      && count=$((count + 1)) \
      || warn "PDF indisponible : ${url}"
  done
  log "CNIL : ${count} guides recuperes dans corpus/raw/cnil/"
}

# --- 3. data.gouv.fr : datasets publics via API ----------------------------
# On interroge l'API, on extrait les URLs de ressources (PDF/CSV/JSON) du
# premier dataset pertinent et on en telecharge quelques-unes.
fetch_open() {
  log "data.gouv.fr : recherche de jeux de donnees..."
  local query="${DATA_QUERY:-intelligence artificielle}"
  local api="https://www.data.gouv.fr/api/1/datasets/?page_size=5&q=${query// /%20}"
  local meta
  meta="$(mktemp)"
  if ! "${CURL[@]}" "${api}" -o "${meta}"; then
    warn "API data.gouv injoignable, on saute cette source."
    rm -f "${meta}"
    return 0
  fi

  # Extraction des 5 premieres URLs de ressources (grep sur le JSON, sans jq pour rester portable).
  local urls
  urls="$(grep -oE 'https://[^"]+\.(pdf|csv|json|txt)' "${meta}" | sort -u | head -n 5)"
  rm -f "${meta}"

  local count=0
  for url in ${urls}; do
    local name
    name="$(basename "${url}" | tr -cd 'A-Za-z0-9._-')"
    [ -z "${name}" ] && name="resource_${count}.bin"
    "${CURL[@]}" "${url}" -o "${RAW_DIR}/data-gouv/${name}" 2>/dev/null \
      && count=$((count + 1)) \
      || warn "Ressource indisponible : ${url}"
  done
  log "data.gouv : ${count} ressources recuperees dans corpus/raw/data-gouv/"
}

# --- Orchestration selon le profil -----------------------------------------
case "${PROFILE}" in
  cert)  fetch_cert ;;
  cnil)  fetch_cnil ;;
  open)  fetch_open ;;
  mixte) fetch_cert; fetch_cnil; fetch_open ;;
  *)     warn "PROFILE inconnu : ${PROFILE} (mixte|cert|cnil|open)"; exit 1 ;;
esac

# --- Bilan -----------------------------------------------------------------
total="$(find "${RAW_DIR}" -type f | wc -l | tr -d ' ')"
log "Termine. ${total} fichiers dans corpus/raw/ (gitignore, non committe)."
log "Le corpus seed committe reste dans corpus/seed/ pour un demarrage offline."
