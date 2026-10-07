"""Build DNS filtering artifacts from a pinned upstream revision and a local allowlist."""
import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "https://github.com/AdguardTeam/HostlistsRegistry.git"
LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")

def allowlist(text):
    domains = set()
    for number, value in enumerate(text.splitlines(), 1):
        value = value.strip()
        if not value or value.startswith("#"):
            continue
        try:
            value = value.rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError:
            raise ValueError(f"invalid allowlist line {number}") from None
        if len(value) > 253 or "." not in value or any(not LABEL.fullmatch(p) for p in value.split(".")):
            raise ValueError(f"invalid allowlist line {number}")
        domains.add(value)
    return sorted(domains)

def prepare(source, exceptions, min_rules=10000):
    # The converter also accepts very small input. Reject upstream error pages and truncation first.
    if re.search(r"(?i)<(?:!doctype|html|body)(?:\s|>)", source):
        raise ValueError("upstream returned HTML")
    count = sum(bool(re.match(r"(?:@@)?\|\|[^\s]+\^", line)) for line in source.splitlines())
    if count < min_rules:
        raise ValueError("upstream DNS rule count below minimum")
    domains = allowlist(exceptions)
    return source.rstrip() + "\n\n! Custom allowlist from zzpice/sing-box-adblock\n" + "".join(f"@@||{name}^\n" for name in domains)

def upstream():
    result = subprocess.run(["git", "ls-remote", UPSTREAM, "refs/heads/main"], capture_output=True, text=True, check=True, timeout=30)
    sha = result.stdout.split()[0] if result.stdout.split() else ""
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("invalid upstream revision")
    url = f"https://raw.githubusercontent.com/AdguardTeam/HostlistsRegistry/{sha}/assets/filter_1.txt"
    request = Request(url, headers={"User-Agent":"zzpice/sing-box-adblock"})
    with urlopen(request, timeout=30) as response:
        if response.headers.get_content_type() != "text/plain":
            raise ValueError("unexpected upstream content type")
        data = response.read(32 * 1024 * 1024 + 1)
    if len(data) > 32 * 1024 * 1024:
        raise ValueError("upstream exceeds size limit")
    return data.decode("utf-8"), sha

def build(binary, source, revision, root=ROOT):
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("invalid upstream revision")
    prepared = prepare(source, (root / "allowlist.txt").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(dir=root, prefix=".adblock-") as directory:
        temporary = Path(directory)
        text, output = temporary / "source.txt", temporary / "adblock.srs"
        with text.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(prepared)
        subprocess.run([str(binary), "rule-set", "convert", "--type", "adguard", "--output", str(output), str(text)], check=True)
        if not output.read_bytes().startswith(b"SRS"):
            raise ValueError("invalid compiled output")
        marker = temporary / "upstream-revision.txt"
        marker.write_text(revision + "\n", encoding="ascii")
        # Even when SRS bytes match, the successful source revision must be recorded.
        for path in (output, marker):
            target = root / path.name
            if not target.exists() or target.read_bytes() != path.read_bytes():
                os.replace(path, target)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sing-box", default="sing-box")
    parser.add_argument("--source", type=Path, help="saved filter_1.txt; requires --revision")
    parser.add_argument("--revision", help="exact source commit for --source")
    args = parser.parse_args()
    if bool(args.source) != bool(args.revision):
        parser.error("--source and --revision must be supplied together")
    try:
        source, revision = (args.source.read_text(encoding="utf-8"), args.revision) if args.source else upstream()
        build(args.sing_box, source, revision)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        raise SystemExit(f"Adblock build failed: {error}") from None
    print("Adblock artifact and upstream revision: OK")
