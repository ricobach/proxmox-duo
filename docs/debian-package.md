## Debian package build

A GitHub Actions workflow at [Build Debian package](https://github.com/ricobach/proxmox-duo/actions/workflows/build-deb.yml)
builds on changes to `main` and can also be launched manually with **Run workflow**.
It compiles and runs tests, builds with `dpkg-deb`, validates the package manifest and
SHA-256 checksum, and commits the resulting `.deb` and checksum to [packages/](../packages/).
No `actions/upload-artifact` step is used.

The package is called **proxmox-duo-diagnostic** (not `proxmox-duo`) to emphasize that
it is **not** a functional Proxmox login extension. It installs only the
`proxmox-duo` diagnostic CLI and Python modules, and makes **no authentication changes**.

On Debian 13 / Proxmox VE 9, a downloaded package can be installed with:

```bash
apt install ./proxmox-duo-diagnostic_0.1.0-1_all.deb
```

The package uses the distribution-provided `python3-duo-client` dependency. It does
not contain API credentials. Create a private configuration file from
`config/duo.example.ini` as described in the project README. Do **not** use this package
for enforcing MFA, or deploy it on production hosts in the expectation that it protects logins.

You can build locally from a Debian/Ubuntu shell with:

```bash
bash scripts/build-deb.sh packages
```

Once the native Proxmox adapter is implemented and tested, it needs its own separately
reviewed package and upgrade/rollback process.
