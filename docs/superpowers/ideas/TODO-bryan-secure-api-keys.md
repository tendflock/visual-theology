# TODO (Bryan): Move API keys out of .env into a secure store

**Captured:** 2026-04-15 during sermon coach MVP execution
**Owner:** Bryan
**Priority:** Before production use of the sermon coach (not before MVP testing)
**Status:** Deferred — placeholder uses .env

## The concern

The sermon coach MVP currently reads three secrets from environment variables:
- `SERMONAUDIO_API_KEY` — pulls Bryan's sermons from his SermonAudio broadcaster account
- `SERMONAUDIO_BROADCASTER_ID` — broadcaster identifier (less sensitive but still account-scoped)
- `ANTHROPIC_API_KEY` — Claude Opus 4.6 calls billed to Bryan's Anthropic account

These are currently expected to live in `tools/workbench/.env` (or the process environment via PM2). `.env` is gitignored, but plaintext secrets on disk are a risk if:
- Disk is backed up to an unencrypted destination
- Files are shared via Time Machine / Dropbox / iCloud Drive without realizing
- A different user on the Mac reads them (single-user shouldn't be at risk, but defense in depth)
- Bryan grants a tool/script disk read access that exfiltrates them

## Recommended approach: macOS Keychain via `keyring`

macOS has a system-level encrypted secret store. Python's `keyring` library has a Keychain backend out of the box.

### Migration path

1. **Install:** `pip install keyring` (already a transitive dep of many tools; safe to add explicitly)

2. **Store secrets** (one-time, run from terminal):
   ```bash
   security add-generic-password -a "$USER" -s "logos4_sermonaudio_api_key" -w "<paste-key-here>"
   security add-generic-password -a "$USER" -s "logos4_sermonaudio_broadcaster_id" -w "<paste-id-here>"
   security add-generic-password -a "$USER" -s "logos4_anthropic_api_key" -w "<paste-key-here>"
   ```
   Or via Python:
   ```python
   import keyring
   keyring.set_password("logos4", "sermonaudio_api_key", "<paste-key-here>")
   keyring.set_password("logos4", "sermonaudio_broadcaster_id", "<paste-id-here>")
   keyring.set_password("logos4", "anthropic_api_key", "<paste-key-here>")
   ```

3. **Add a tiny `secrets.py` shim** at `tools/workbench/secrets.py`:
   ```python
   """Secret loader. Tries Keychain first, falls back to env vars for tests/CI."""
   import os
   try:
       import keyring
       _kr = keyring
   except ImportError:
       _kr = None

   _SERVICE = "logos4"

   def get_secret(name: str, env_var: str = None) -> str:
       """Return secret by logical name. Keychain wins; env var is fallback."""
       if _kr is not None:
           value = _kr.get_password(_SERVICE, name)
           if value:
               return value
       if env_var:
           return os.environ.get(env_var, "")
       return ""

   def sermonaudio_api_key() -> str:
       return get_secret("sermonaudio_api_key", "SERMONAUDIO_API_KEY")

   def sermonaudio_broadcaster_id() -> str:
       return get_secret("sermonaudio_broadcaster_id", "SERMONAUDIO_BROADCASTER_ID")

   def anthropic_api_key() -> str:
       return get_secret("anthropic_api_key", "ANTHROPIC_API_KEY")
   ```

4. **Update the three callsites** in `tools/workbench/app.py` (added in Task 18):

   ```python
   # Before:
   def _broadcaster_id() -> str:
       return _os_for_sync.environ.get('SERMONAUDIO_BROADCASTER_ID', '')

   def _make_sermonaudio_client():
       from sermonaudio_sync import SermonAudioAPIClient
       api_key = _os_for_sync.environ.get('SERMONAUDIO_API_KEY', '')
       return SermonAudioAPIClient(api_key)

   # After:
   from secrets import sermonaudio_api_key, sermonaudio_broadcaster_id, anthropic_api_key

   def _broadcaster_id() -> str:
       return sermonaudio_broadcaster_id()

   def _make_sermonaudio_client():
       from sermonaudio_sync import SermonAudioAPIClient
       return SermonAudioAPIClient(sermonaudio_api_key())
   ```
   And in `sermon_reanalyze` and `sermon_coach_message` routes, replace
   `_os_for_sync.environ.get('ANTHROPIC_API_KEY', '')` with `anthropic_api_key()`.

5. **Verify**:
   ```bash
   python3 -c "import sys; sys.path.insert(0,'tools/workbench'); from secrets import sermonaudio_api_key; print('ok' if sermonaudio_api_key() else 'EMPTY')"
   ```
   Should print `ok` if Keychain is wired correctly.

6. **Delete the .env entries** for these three keys after Keychain is verified working.

7. **Tests still work** because `secrets.py` falls back to env vars when Keychain isn't available or returns nothing — CI/test environments can still pass keys via env (or use mocked clients, which is the actual MVP test pattern).

## Alternative: 1Password CLI

If Bryan uses 1Password, the equivalent is:

```python
import subprocess
def get_secret(item, field='credential'):
    return subprocess.check_output(['op', 'read', f'op://Private/{item}/{field}']).decode().strip()

def sermonaudio_api_key():
    return get_secret('SermonAudio API Key')
```

This requires the 1Password app to be running and unlocked, and the `op` CLI installed. Slightly more friction than Keychain but stronger isolation if you want to share/rotate via 1Password's web UI.

## Alternative: macOS Launch Agent + restricted env file

If Bryan wants to keep .env semantics but harden it, he can:
- Move `.env` to `~/Library/Application Support/logos4/.env`
- `chmod 600 ~/Library/Application Support/logos4/.env`
- Update PM2 process to source it from there

This is the lowest-effort hardening but doesn't touch encryption — it only restricts file permissions.

## What NOT to do

- Don't commit secrets to git in any form, even gitignored — git history can leak.
- Don't use macOS environment variables set in `~/.zshrc` or `~/.bash_profile` — they're plaintext on disk and inherited by any child process Bryan launches in any terminal.
- Don't store secrets in the SQLite `companion.db` — it's gitignored but lives in the repo working directory and would be backed up to the same places as the rest of the project.

## When to do this

**Before**: any of these scenarios:
- Bryan starts using the sermon coach against his real SermonAudio account in production
- Bryan grants any new tool (web AI service, screen sharing, remote pair, etc.) access to his Mac's filesystem
- Anyone else gets access to this Mac
- Bryan's API keys get rotated for any reason (good time to migrate during the rotation)

**After**: MVP testing with mocked clients (current state) — that doesn't touch real keys at all.

## How to mark this done

Once Bryan has migrated:
1. Delete this file
2. Make sure the three `_os_for_sync.environ.get('SERMONAUDIO_API_KEY', ...)` etc. callsites in `tools/workbench/app.py` are gone
3. Run `grep -r 'SERMONAUDIO_API_KEY\|ANTHROPIC_API_KEY' tools/workbench/` and confirm only `secrets.py` references them
