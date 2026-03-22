"""
Persistent batch connection to LogosReader for efficient multi-resource reading.

Instead of spawning a new dotnet process for each read (expensive startup),
this keeps a single LogosReader process alive in --batch mode and sends
commands over stdin, reading results from stdout delimited by '---END---'.

Usage:
    with LogosBatchReader() as reader:
        text = reader.read_article("ESV.logos4", 42, max_chars=50000)
        articles = reader.list_articles("KJV1900.logos4")
"""

import os
import subprocess
import sys
import threading
import time

# ── Configuration (same as study.py) ─────────────────────────────────────

DOTNET_ENV = {
    **os.environ,
    "PATH": f"/opt/homebrew/opt/dotnet@8/bin:/usr/bin:/bin:{os.environ.get('PATH', '')}",
    "DOTNET_ROOT": "/opt/homebrew/opt/dotnet@8/libexec",
}
READER_DIR = "/Volumes/External/Logos4/tools/LogosReader"


class LogosBatchReader:
    """Persistent connection to LogosReader for efficient multi-read operations.

    The underlying dotnet process is started once in --batch mode and kept
    alive for the lifetime of the reader.  Commands are sent on stdin and
    results are read from stdout, with each result terminated by a line
    containing only '---END---'.

    Use as a context manager::

        with LogosBatchReader() as reader:
            text = reader.read_article("ESV.logos4", 42)
    """

    END_MARKER = "---END---"

    def __init__(self, startup_timeout=60):
        """Start the LogosReader process in batch mode.

        Args:
            startup_timeout: seconds to wait for the process to become ready.
        """
        self._proc = None
        self._lock = threading.Lock()
        self._stderr_lines = []
        self._stderr_thread = None
        self._start_process(startup_timeout)

    # ── Public API ────────────────────────────────────────────────────────

    def read_article(self, resource_file, article_num, max_chars=50000):
        """Read a single article from a resource.

        Args:
            resource_file: e.g. "ESV.logos4" (bare filename or full path)
            article_num: integer article number
            max_chars: maximum characters to read

        Returns:
            Article text as a string, or None on failure.
        """
        result = self._send_command(f"read {resource_file} {article_num} {max_chars}")
        return result if result else None

    def list_articles(self, resource_file):
        """List all articles in a resource.

        Returns:
            List of (article_num, article_id) tuples, or empty list on failure.
        """
        result = self._send_command(f"list {resource_file}")
        if not result:
            return []
        articles = []
        for line in result.split("\n"):
            parts = line.split("\t")
            if len(parts) == 2:
                try:
                    num = int(parts[0])
                    articles.append((num, parts[1]))
                except ValueError:
                    # Skip header line "Article#\tArticleId"
                    pass
        return articles

    def get_info(self, resource_file):
        """Get resource info.

        Returns:
            Dict with keys like ResourceId, Version, DriverVersion, ArticleCount.
            Returns empty dict on failure.
        """
        result = self._send_command(f"info {resource_file}")
        if not result:
            return {}
        info = {}
        for line in result.split("\n"):
            if ": " in line:
                key, _, value = line.partition(": ")
                key = key.strip()
                value = value.strip()
                if key == "ArticleCount":
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                info[key] = value
        return info

    def get_toc(self, resource_file):
        """Get table of contents for a resource.

        Returns:
            Raw TOC text, or None on failure.
        """
        result = self._send_command(f"toc {resource_file}")
        return result if result else None

    def get_interlinear(self, resource_file, article_num):
        """Get interlinear data for a Bible article.

        Args:
            resource_file: e.g. "ESV.logos4"
            article_num: integer article number

        Returns:
            Raw TSV text (header + word rows), or None on failure.
        """
        result = self._send_command(f"interlinear {resource_file} {article_num}")
        return result if result else None

    def get_navigation_index(self, resource_file):
        """Get the navigation index (reference→article mapping) for a resource.

        Returns dict with keys:
            'references': list of {'ref': str, 'article': int, 'offset': int}
            'topics': list of {'key': str, 'name': str, 'article': int, 'offset': int}
        """
        stdout = self._send_command(f"navindex {resource_file}")
        refs = []
        topics = []
        if stdout:
            for line in stdout.split("\n"):
                parts = line.split("\t")
                if len(parts) >= 4 and parts[0] == "REF":
                    try:
                        refs.append({"ref": parts[1], "article": int(parts[2]), "offset": int(parts[3])})
                    except ValueError:
                        pass
                elif len(parts) >= 5 and parts[0] == "TOPIC":
                    try:
                        topics.append({"key": parts[1], "name": parts[2], "article": int(parts[3]), "offset": int(parts[4])})
                    except ValueError:
                        pass
        return {"references": refs, "topics": topics}

    def get_article_title(self, resource_file, article_num):
        """Get the title of an article.

        Returns title string (with Unicode language tags stripped), or None.
        """
        stdout = self._send_command(f"article-title {resource_file} {article_num}")
        if not stdout:
            return None
        title = stdout.strip()
        # Strip Unicode language tag characters (U+E0000-U+E007F)
        title = "".join(c for c in title if not (0xE0000 <= ord(c) <= 0xE007F))
        return title if title else None

    def find_article(self, resource_file, pattern):
        """Search article IDs for a pattern.

        Args:
            resource_file: resource filename
            pattern: search string (case-insensitive substring match)

        Returns:
            List of (article_num, article_id) tuples matching the pattern.
        """
        # Quote the pattern in case it contains spaces
        quoted_pattern = f'"{pattern}"' if " " in pattern else pattern
        result = self._send_command(f"find-article {resource_file} {quoted_pattern}")
        if not result:
            return []
        articles = []
        for line in result.split("\n"):
            parts = line.split("\t")
            if len(parts) == 2:
                try:
                    num = int(parts[0])
                    articles.append((num, parts[1]))
                except ValueError:
                    pass
        return articles

    def query_dataset(self, resource_file, db_name, sql, max_rows=500):
        """Query an encrypted volume's embedded SQLite database.

        Args:
            resource_file: e.g. "FIGURATIVE-LANGUAGE.lbssd"
            db_name: e.g. "SupplementalData.db"
            sql: SQL query string

        Returns:
            List of dicts (column_name → value), or empty list on failure.
        """
        # SQL must be double-quoted so ParseCommandLine treats it as one token.
        # Replace internal double-quotes with single-quotes (safe for SQLite).
        sql_safe = sql.replace('"', "'")
        result = self._send_command(f'query-db {resource_file} {db_name} "{sql_safe}"')
        if not result:
            return []

        lines = result.strip().split('\n')
        if len(lines) < 1:
            return []

        # First line is tab-separated column headers
        headers = lines[0].split('\t')
        rows = []
        for line in lines[1:]:
            if not line.strip():
                continue
            vals = line.split('\t')
            row = {}
            for i, h in enumerate(headers):
                row[h] = vals[i] if i < len(vals) else ""
            rows.append(row)
            if len(rows) >= max_rows:
                break

        return rows

    def volume_info(self, resource_file):
        """Get metadata for an encrypted volume.

        Returns:
            Dict with ResourceId and DriverName, or None on failure.
        """
        result = self._send_command(f'volume-info {resource_file}')
        if not result:
            return None

        info = {}
        for line in result.strip().split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                info[key.strip()] = val.strip()
        return info

    def is_alive(self):
        """Check if the underlying process is still running."""
        return self._proc is not None and self._proc.poll() is None

    def close(self):
        """Shut down the reader process gracefully."""
        if self._proc is None:
            return
        try:
            if self._proc.poll() is None:
                # Send empty line to trigger exit
                try:
                    self._proc.stdin.write("\n")
                    self._proc.stdin.flush()
                except (BrokenPipeError, OSError):
                    pass
                try:
                    self._proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
                    self._proc.wait(timeout=5)
        except Exception:
            try:
                self._proc.kill()
            except Exception:
                pass
        finally:
            self._proc = None
            if self._stderr_thread is not None:
                self._stderr_thread.join(timeout=5)
                self._stderr_thread = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    # ── Internal ──────────────────────────────────────────────────────────

    def _start_process(self, timeout):
        """Launch the dotnet process and wait for it to be ready."""
        cmd = ["dotnet", "run", "--", "--batch"]
        self._proc = subprocess.Popen(
            cmd,
            cwd=READER_DIR,
            env=DOTNET_ENV,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )

        # Start a background thread to drain stderr so it doesn't block
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr, daemon=True
        )
        self._stderr_thread.start()

        # Wait until we see the "Batch mode ready" message on stderr
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._proc.poll() is not None:
                raise RuntimeError(
                    f"LogosReader process exited during startup (code {self._proc.returncode}). "
                    f"stderr: {''.join(self._stderr_lines[-20:])}"
                )
            # Check if ready message appeared
            for line in self._stderr_lines:
                if "Batch mode ready" in line:
                    return
            time.sleep(0.2)

        raise TimeoutError(
            f"LogosReader did not become ready within {timeout}s. "
            f"stderr: {''.join(self._stderr_lines[-20:])}"
        )

    def _drain_stderr(self):
        """Background thread: read stderr lines and store them."""
        try:
            for line in self._proc.stderr:
                self._stderr_lines.append(line)
                # Optional: print to our stderr for debugging
                # print(line, end="", file=sys.stderr)
        except (ValueError, OSError):
            pass  # Process closed

    def _send_command(self, command, timeout=120):
        """Send a command and read the response up to the ---END--- marker.

        Args:
            command: command string to send (without trailing newline)
            timeout: seconds to wait for the response

        Returns:
            Response text (may be empty string), or None if the process died.

        Raises:
            TimeoutError: if no response within timeout seconds.
            RuntimeError: if the process has died.
        """
        with self._lock:
            if not self.is_alive():
                raise RuntimeError("LogosReader process is not running.")

            try:
                self._proc.stdin.write(command + "\n")
                self._proc.stdin.flush()
            except (BrokenPipeError, OSError) as e:
                raise RuntimeError(f"Failed to send command: {e}")

            return self._read_until_end(timeout)

    def _read_until_end(self, timeout):
        """Read stdout lines until we see ---END---, with a timeout."""
        lines = []
        deadline = time.time() + timeout

        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError(
                    f"Timed out waiting for response. Got so far: {''.join(lines[:5])}"
                )

            # Check if process died
            if self._proc.poll() is not None:
                # Try to read remaining output
                try:
                    rest = self._proc.stdout.read()
                    if rest:
                        lines.append(rest)
                except Exception:
                    pass
                raise RuntimeError(
                    f"LogosReader process died (code {self._proc.returncode}). "
                    f"Partial output: {''.join(lines[:5])}"
                )

            # Read one line (blocking, but process should respond)
            # We use a thread with a timeout to avoid infinite blocking
            line = self._readline_with_timeout(remaining)
            if line is None:
                # Timeout on readline
                raise TimeoutError(
                    f"Timed out reading response line. Got so far: {''.join(lines[:5])}"
                )

            if line.rstrip("\n").rstrip("\r") == self.END_MARKER:
                break

            lines.append(line)

        # Join and strip trailing whitespace
        result = "".join(lines).rstrip("\n").rstrip("\r")
        return result

    def _readline_with_timeout(self, timeout):
        """Read a single line from stdout with a timeout.

        Returns the line, or None on timeout.
        """
        result = [None]

        def _read():
            try:
                result[0] = self._proc.stdout.readline()
            except (ValueError, OSError):
                pass

        t = threading.Thread(target=_read, daemon=True)
        t.start()
        t.join(timeout=timeout)

        if t.is_alive():
            # Thread is still blocking on readline - timeout
            return None

        return result[0]


# ── Convenience / CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    # Quick smoke test
    print("Starting LogosBatchReader...", file=sys.stderr)
    try:
        with LogosBatchReader() as reader:
            print("Reader started successfully.", file=sys.stderr)

            # Test with a common resource if available
            if len(sys.argv) >= 2:
                resource = sys.argv[1]
                print(f"Getting info for {resource}...", file=sys.stderr)
                info = reader.get_info(resource)
                for k, v in info.items():
                    print(f"  {k}: {v}")

                print(f"Listing articles for {resource}...", file=sys.stderr)
                articles = reader.list_articles(resource)
                print(f"  Found {len(articles)} articles")
                for num, aid in articles[:10]:
                    print(f"  {num}\t{aid}")
                if len(articles) > 10:
                    print(f"  ... ({len(articles) - 10} more)")
            else:
                print("Usage: python3 logos_batch.py <resource_file>", file=sys.stderr)
                print("  e.g.: python3 logos_batch.py ESV.logos4", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
