"""Audit sensitive residue (real name, private paths, private numbers) and
guard the public repo against re-introducing them.

Usage:
    python _audit_sensitive_residue.py        # exit 0 if clean, 1 if hits
    python _audit_sensitive_residue.py --ci   # CI mode, GitHub Actions annotations

Scans only files that are present in `git ls-files` (i.e., what would actually
be published) and ignores itself (its regex patterns are naturally matches).
Emits GitHub-Actions-friendly `::error file=...,line=...` annotations in CI mode.
"""
import re
import subprocess
import sys
from pathlib import Path

# === Patterns to forbid in the public mirror ===
# (regex, label, severity). Severity drives exit code & annotation level.
PATTERNS = [
    (r'E:\\peS2o_kb_faiss', 'private KB path', 'high'),
    (r'541,733', 'private KB scale', 'high'),
    (r'541,713', 'private KB scale', 'high'),
    (r'刘泽文', 'private real name', 'high'),
    (r'齐鲁', 'private school prefix', 'high'),
    (r'枣庄', 'private school city', 'high'),
    (r'泰玄小站', 'private project name', 'medium'),
    (r'泰玄', 'private project name', 'medium'),
    (r'116\.62\.69\.83', 'private server IP', 'medium'),
    (r'wanxiangapp', 'private domain', 'low'),
    (r'2038796100751', 'private ICP filing number', 'medium'),
    (r'163\.com|qq\.com', 'private email-domain substring', 'low'),
    (r'47\.98\.106\.182', 'private server IP', 'medium'),
]

SCAN_EXTS = ('.py', '.md', '.json', '.sh', '.log', '.txt', '.yml', '.yaml', '.toml')
MAX_FILE_BYTES = 4 * 1024 * 1024  # 4 MB cap; large JSON files shouldn't have these
SELF_NAME = '_audit_sensitive_residue.py'


def git_tracked_files():
    """List all files that git would publish (respects .gitignore)."""
    try:
        out = subprocess.check_output(
            ['git', 'ls-files'], cwd='.', stderr=subprocess.DEVNULL)
        return [Path(line.strip()) for line in out.decode().splitlines()
                if line.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None  # not a git checkout; fall back to walk-and-filter


def emit_gh_annotations(hits):
    """Emit GitHub Actions ::error annotations for each finding."""
    for label, occurrences in hits.items():
        for fname, lineno, snippet in occurrences[:20]:  # cap annotations per pattern
            print(f'::error file={fname},line={lineno},title=Sensitive residue '
                  f'({label})::Found banned pattern; please redact. '
                  f'Snippet: {snippet[:80]!r}')


def main():
    ci_mode = '--ci' in sys.argv

    tracked = git_tracked_files()
    if tracked is None:
        print('NOTICE: not a git checkout; scanning working tree '
              'as a fallback (ignores .gitignore).', file=sys.stderr)
        candidates = [p for p in Path('.').rglob('*') if p.is_file()]
    else:
        candidates = tracked

    # Filter to scannable text files. Skip self.
    files = [p for p in candidates
             if p.name != SELF_NAME
             and p.suffix in SCAN_EXTS
             and p.is_file()
             and p.stat().st_size <= MAX_FILE_BYTES]

    hits = {}
    for f in files:
        try:
            text = f.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for pattern, label, _sev in PATTERNS:
                m = re.search(pattern, line)
                if m:
                    hits.setdefault(label, []).append(
                        (f.as_posix(), line_no, line.strip()[:120]))

    total = sum(len(v) for v in hits.values())
    if not hits:
        print(f'OK: scanned {len(files)} file(s); 0 sensitive-residue hits.')
        return 0

    print(f'FAIL: scanned {len(files)} file(s); {total} hit(s) across '
          f'{len(hits)} pattern(s):')
    for label, occurrences in hits.items():
        print(f'\n[{label}]  ({len(occurrences)} occurrence(s))')
        for fname, ln, snippet in occurrences[:5]:
            print(f'   {fname}:{ln}  {snippet!r}')
        if len(occurrences) > 5:
            print(f'   ... and {len(occurrences) - 5} more')

    if ci_mode:
        emit_gh_annotations(hits)
    return 1


if __name__ == '__main__':
    sys.exit(main())
