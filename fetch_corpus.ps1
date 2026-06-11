# fetch_corpus.ps1 - Version Windows/PowerShell du script de recuperation de corpus.
# Equivalent de fetch_corpus.sh. Sources publiques a licence ouverte (CERT-FR, CNIL, data.gouv).
#
# Usage :
#   ./fetch_corpus.ps1                       # profil mixte (~30 docs)
#   ./fetch_corpus.ps1 -Profile cert         # projet B : avis CERT-FR
#   ./fetch_corpus.ps1 -Profile cnil         # projet C : guides CNIL
#   ./fetch_corpus.ps1 -Profile open         # projet A : data.gouv
#   ./fetch_corpus.ps1 -NAvis 40             # nb d'avis CERT-FR

param(
    [ValidateSet("mixte", "cert", "cnil", "open")]
    [string]$Profile = "mixte",
    [int]$NAvis = 30,
    [string]$DataQuery = "intelligence artificielle"
)

$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$RawDir = Join-Path $Here "corpus/raw"
New-Item -ItemType Directory -Force -Path "$RawDir/cert-fr", "$RawDir/cnil", "$RawDir/data-gouv" | Out-Null

function Get-File($Url, $OutFile) {
    try {
        Invoke-WebRequest -Uri $Url -OutFile $OutFile -UseBasicParsing -TimeoutSec 30 `
            -Headers @{ "User-Agent" = "tp-rag-formation/1.0" }
        return $true
    } catch {
        Write-Warning "Indisponible : $Url"
        return $false
    }
}

function Fetch-Cert {
    Write-Host "[fetch] CERT-FR : recuperation du flux d'avis..." -ForegroundColor Cyan
    $feed = Join-Path $env:TEMP "certfr_feed.xml"
    if (-not (Get-File "https://www.cert.ssi.gouv.fr/avis/feed/" $feed)) { return }
    $content = Get-Content $feed -Raw
    $ids = [regex]::Matches($content, "CERTFR-\d{4}-AVI-\d{4}") |
        ForEach-Object { $_.Value } | Select-Object -Unique | Select-Object -First $NAvis
    $count = 0
    foreach ($id in $ids) {
        $base = "https://www.cert.ssi.gouv.fr/avis/$id"
        if (Get-File "$base/json/" "$RawDir/cert-fr/$id.json") { $count++ }
        Get-File "$base/" "$RawDir/cert-fr/$id.html" | Out-Null
    }
    Remove-Item $feed -ErrorAction SilentlyContinue
    Write-Host "[fetch] CERT-FR : $count avis recuperes." -ForegroundColor Cyan
}

function Fetch-Cnil {
    Write-Host "[fetch] CNIL : recuperation des guides RGPD (PDF)..." -ForegroundColor Cyan
    $urls = @(
        "https://www.cnil.fr/sites/default/files/atoms/files/cnil_guide_securite_des_donnees_personnelles-2023.pdf",
        "https://www.cnil.fr/sites/default/files/atoms/files/bpi-cnil-rgpd_guide-tpe-pme.pdf",
        "https://www.cnil.fr/sites/default/files/atoms/files/rgpd-guide_sous-traitant-cnil.pdf"
    )
    $count = 0
    foreach ($url in $urls) {
        $name = Split-Path $url -Leaf
        if (Get-File $url "$RawDir/cnil/$name") { $count++ }
    }
    Write-Host "[fetch] CNIL : $count guides recuperes." -ForegroundColor Cyan
}

function Fetch-Open {
    Write-Host "[fetch] data.gouv.fr : recherche de jeux de donnees..." -ForegroundColor Cyan
    $q = [uri]::EscapeDataString($DataQuery)
    $api = "https://www.data.gouv.fr/api/1/datasets/?page_size=5&q=$q"
    $meta = Join-Path $env:TEMP "datagouv.json"
    if (-not (Get-File $api $meta)) { return }
    $content = Get-Content $meta -Raw
    $urls = [regex]::Matches($content, "https://[^`"]+\.(pdf|csv|json|txt)") |
        ForEach-Object { $_.Value } | Select-Object -Unique | Select-Object -First 5
    $count = 0
    foreach ($url in $urls) {
        $name = (Split-Path $url -Leaf) -replace "[^A-Za-z0-9._-]", ""
        if (-not $name) { $name = "resource_$count.bin" }
        if (Get-File $url "$RawDir/data-gouv/$name") { $count++ }
    }
    Remove-Item $meta -ErrorAction SilentlyContinue
    Write-Host "[fetch] data.gouv : $count ressources recuperees." -ForegroundColor Cyan
}

switch ($Profile) {
    "cert"  { Fetch-Cert }
    "cnil"  { Fetch-Cnil }
    "open"  { Fetch-Open }
    "mixte" { Fetch-Cert; Fetch-Cnil; Fetch-Open }
}

$total = (Get-ChildItem -Recurse -File $RawDir | Measure-Object).Count
Write-Host "[fetch] Termine. $total fichiers dans corpus/raw/ (gitignore)." -ForegroundColor Green
