# Repository Guidelines

## Project Structure & Module Organization
This repository contains a Logos 4 library integration and sermon study companion. Core Python tooling lives in `tools/`, with the Flask workbench app under `tools/workbench/`:

- `tools/workbench/app.py`: Flask routes and local app entrypoint.
- `tools/workbench/templates/`: Jinja/HTML templates.
- `tools/workbench/static/`: CSS and browser JavaScript.
- `tools/workbench/tests/`: pytest test suite.
- `tools/LogosReader/`: C# reader used by the Logos access layer.
- `docs/`: research, plans, specs, and handoffs.
- `scripts/`: standalone maintenance or analysis scripts.

## Build, Test, and Development Commands
Set .NET paths before working with the C# reader:

```bash
export PATH="/opt/homebrew/opt/dotnet@8/bin:$PATH"
export DOTNET_ROOT="/opt/homebrew/opt/dotnet@8/libexec"
```

Run the web app locally:

```bash
cd tools/workbench && python3 app.py
```

The app serves `http://localhost:5111/` and `/companion/`.

Run tests:

```bash
cd tools/workbench && python3 -m pytest tests/ -v
```

Build or run the C# reader when changing `tools/LogosReader/`:

```bash
dotnet build tools/LogosReader/LogosReader.csproj
dotnet run --project tools/LogosReader/LogosReader.csproj
```

## Coding Style & Naming Conventions
Use Python 3 with 4-space indentation and descriptive `snake_case` names. Keep Flask routes thin; place retrieval, ranking, parsing, and agent behavior in dedicated modules such as `companion_tools.py`, `sermon_matcher.py`, or `llm_client.py`. Name tests `test_*.py` and prefer focused fixtures in `tools/workbench/tests/conftest.py`. For frontend changes, keep CSS in `static/` and templates in `templates/`.

## Testing Guidelines
The test suite uses pytest. Add or update tests for changed route behavior, data access, parsing, agent/tool contracts, and regressions. Tests marked `e2e` use Playwright; tests marked `tools` may require `ANTHROPIC_API_KEY`. Run the targeted test first, then the full workbench suite when practical.

## Commit & Pull Request Guidelines
Recent history uses concise conventional prefixes such as `feat:`, `fix:`, `docs:`, and `chore:`. Keep commits scoped and imperative, for example `fix: validate sermon sync input`. Pull requests should describe the change, list tests run, call out environment or service needs, and include screenshots for UI changes.

## Security & Configuration Tips
Do not commit API keys, license data, generated caches, or local database contents. Treat `Data/`, `Users/`, `Shared/`, and `Logging/` as local Logos/library state unless a change is explicit. Prefer environment variables for credentials and document new configuration in `docs/` or this guide.
