# Logos 4 Library Project

## Allowed Commands
The following commands should be run without asking for permission:
- `export` (environment variables like PATH, DOTNET_ROOT)
- `sqlite3` (querying catalog.db, ResourceManager.db, logos_cache.db)
- `python3 -c` (one-liner Python scripts)
- `python3 tools/*.py` (running project Python scripts)
- `dotnet build` and `dotnet run` (building/running LogosReader)
- `ls`, `wc`, `file`, `xxd`, `hexdump` (file inspection)

## Environment Setup
```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
```

## Key Paths
- Catalog DB: `Data/e3txalek.5iq/LibraryCatalog/catalog.db`
- ResourceManager DB: `Data/e3txalek.5iq/ResourceManager/ResourceManager.db`
- Resources: `Data/e3txalek.5iq/ResourceManager/Resources/`
- Licenses: `Data/e3txalek.5iq/LicenseManager/`
- LogosReader: `tools/LogosReader/Program.cs`
- User ID: `5621617`
