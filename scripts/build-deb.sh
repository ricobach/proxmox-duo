#!/usr/bin/env bash
set -euo pipefail

# Build a diagnostic-only Debian package; no Proxmox authentication hooks.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
VERSION="$(python3 - <<'PY'
import pathlib, re
content = pathlib.Path("pyproject.toml").read_text()
match = re.search(r'^version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"\s*$', content, re.M)
if match is None:
    raise SystemExit("Could not read semantic project version")
print(match.group(1))
PY
)"
PKG="proxmox-duo-diagnostic"
REVISION="1"
DEST="${1:-packages}"
mkdir -p "$DEST"
DEST="$(realpath "$DEST")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
chmod 0755 "$TMP"

install -d -m 0755 "$TMP/DEBIAN" "$TMP/usr/bin" \
  "$TMP/usr/lib/python3/dist-packages/proxmox_duo" \
  "$TMP/usr/share/doc/$PKG"
install -m 0644 proxmox_duo/__init__.py proxmox_duo/push.py proxmox_duo/cli.py \
  "$TMP/usr/lib/python3/dist-packages/proxmox_duo/"
install -m 0644 README.md "$TMP/usr/share/doc/$PKG/README"
install -m 0644 LICENSE "$TMP/usr/share/doc/$PKG/copyright"
cat > "$TMP/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION-$REVISION
Section: admin
Priority: optional
Architecture: all
Maintainer: Proxmox Duo contributors
Depends: python3 (>= 3.11), python3-duo-client (>= 5.0)
Description: Experimental Duo Push API diagnostics (not Proxmox MFA)
 Sends a test Duo Push and checks its result. Does NOT integrate with
 Proxmox authentication, require Duo for login, or change PAM settings.
EOF
cat > "$TMP/usr/bin/proxmox-duo" <<'EOF'
#!/usr/bin/python3
from proxmox_duo.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
EOF
chmod 0755 "$TMP/usr/bin/proxmox-duo"

OUTPUT="$DEST/${PKG}_${VERSION}-${REVISION}_all.deb"
dpkg-deb --build --root-owner-group "$TMP" "$OUTPUT"
dpkg-deb --info "$OUTPUT"
dpkg-deb --contents "$OUTPUT"
printf '%s  %s\n' "$(sha256sum "$OUTPUT" | cut -d' ' -f1)" "$(basename "$OUTPUT")" > "$OUTPUT.sha256"
echo "Built $OUTPUT"
