$ErrorActionPreference = "Stop"

# Imports the fake/demo seed JSON into a running local MongoDB instance on Windows PowerShell.
# Usage:
#   docker compose -f compose.yml up -d mongo
#   .\scripts\import_seed.ps1

$DbName = if ($env:MONGO_DB_NAME) { $env:MONGO_DB_NAME } else { "CougarWorks" }
$MongoUser = if ($env:MONGO_USER) { $env:MONGO_USER } else { "cougarworks_app" }
$MongoPass = if ($env:MONGO_PASS) { $env:MONGO_PASS } else { "change-this-mongo-password" }
$MongoHost = if ($env:MONGO_HOST) { $env:MONGO_HOST } else { "localhost" }
$MongoPort = if ($env:MONGO_PORT) { $env:MONGO_PORT } else { "27017" }
$AuthDb = if ($env:MONGO_AUTH_DB) { $env:MONGO_AUTH_DB } else { "admin" }
$SeedDir = if ($env:SEED_DIR) { $env:SEED_DIR } else { "database/seeds" }

Get-ChildItem "$SeedDir\*.json" | ForEach-Object {
    $collection = $_.BaseName
    Write-Host "Importing $($_.FullName) into $DbName.$collection"
    mongoimport `
      --host $MongoHost `
      --port $MongoPort `
      --username $MongoUser `
      --password $MongoPass `
      --authenticationDatabase $AuthDb `
      --db $DbName `
      --collection $collection `
      --jsonArray `
      --drop `
      --file $_.FullName
}

Write-Host "Seed import complete."
