<#
    import_to_turso.ps1
    ====================
    Importe data\centropuertas.db dans Turso via l'API Platform HTTP
    (aucune installation de CLI necessaire -- juste curl.exe, deja
    fourni par Windows 10/11).

    A LANCER SOI-MEME dans un terminal PowerShell (pas via un
    assistant IA) : les deux variables ci-dessous contiennent des
    secrets qui ne doivent jamais transiter par un chat.

    AVANT de lancer ce script, dans CETTE fenetre PowerShell :

        $env:TURSO_API_TOKEN = "...."   # Dashboard Turso > Account Settings > API Tokens
        $env:TURSO_ORG_SLUG  = "...."   # visible dans l'URL du dashboard Turso (app.turso.tech/<org-slug>)

    Puis :

        cd centropuertas_v2
        .\scripts\import_to_turso.ps1

    Le token propre a la base nouvellement creee est ecrit dans
    data\turso_token.txt (deja exclu de git par .gitignore) -- ne le
    partage jamais, c'est l'equivalent d'un mot de passe pour accéder
    a toutes les donnees de tous les techniciens.
#>

$ErrorActionPreference = "Stop"

if (-not $env:TURSO_API_TOKEN) {
    throw 'Definis d''abord $env:TURSO_API_TOKEN (Turso dashboard > Account Settings > API Tokens).'
}
if (-not $env:TURSO_ORG_SLUG) {
    throw 'Definis d''abord $env:TURSO_ORG_SLUG (visible dans l''URL du dashboard Turso).'
}

$DbName = "centropuertas"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$DbFile = Join-Path $ProjectRoot "data\centropuertas.db"
$TokenFile = Join-Path $ProjectRoot "data\turso_token.txt"

if (-not (Test-Path $DbFile)) {
    throw "Base introuvable : $DbFile"
}

Write-Host "1) Checkpoint WAL (fusionne centropuertas.db-wal dans le fichier principal)..."
python -c "import sqlite3; c = sqlite3.connect(r'$DbFile'); c.execute('PRAGMA wal_checkpoint(TRUNCATE)'); c.close()"

Write-Host "2) Creation de la base Turso '$DbName' (seed = database_upload)..."
$createJson = '{"name":"' + $DbName + '","group":"default","seed":{"type":"database_upload"}}'
$createResp = curl.exe -sS -X POST "https://api.turso.tech/v1/organizations/$env:TURSO_ORG_SLUG/databases" `
    -H "Authorization: Bearer $env:TURSO_API_TOKEN" `
    -H "Content-Type: application/json" `
    -d $createJson

$create = $createResp | ConvertFrom-Json
if (-not $create.database) {
    Write-Host $createResp
    throw "Echec de la creation de la base (reponse ci-dessus) -- verifie TURSO_ORG_SLUG et TURSO_API_TOKEN, et qu'aucune base 'centropuertas' n'existe deja."
}
$hostname = $create.database.Hostname
Write-Host "   -> hostname: $hostname"

Write-Host "3) Generation d'un token propre a cette base..."
$tokenResp = curl.exe -sS -X POST "https://api.turso.tech/v1/organizations/$env:TURSO_ORG_SLUG/databases/$DbName/auth/tokens" `
    -H "Authorization: Bearer $env:TURSO_API_TOKEN"
$dbToken = ($tokenResp | ConvertFrom-Json).jwt
if (-not $dbToken) {
    Write-Host $tokenResp
    throw "Echec de la generation du token de base."
}

Write-Host "4) Upload de centropuertas.db ($((Get-Item $DbFile).Length) octets)..."
$size = (Get-Item $DbFile).Length
curl.exe -sS -X POST "https://$hostname/v1/upload" `
    -H "Authorization: Bearer $dbToken" `
    -H "Content-Length: $size" `
    --data-binary "@$DbFile" | Out-Null

Set-Content -Path $TokenFile -Value $dbToken -NoNewline
Write-Host ""
Write-Host "OK - base 'centropuertas' importee sur Turso."
Write-Host "Hostname     : $hostname"
Write-Host "URL libsql   : libsql://$hostname"
Write-Host "Token de base: ecrit dans $TokenFile (NE PAS partager ni committer)."
