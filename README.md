# Proxmox Duo

Experimental Duo Push-only integration for Proxmox VE PAM web authentication.

> **Development status:** This repository is not a working Proxmox authentication extension yet. Do not deploy it to a production hypervisor. No changes to PAM, `pveproxy`, Proxmox login code, or ticket issuance are installed by this project.

## Goal

Keep Proxmox `@pam` primary authentication intact, require a Duo Push approval **before** a normal Proxmox web session ticket is issued, and display waiting/approved/denied/expired status in the login UI. No Duo Authentication Proxy, SMS, OTP, calls, or optional bypass.

## Initial milestone

A small Python Duo Auth API client, a restricted standalone CLI for connection testing and optional Push testing, a sample configuration, and unit tests. The native Proxmox ticket/TFA challenge integration remains future work and is **not** security-enforcing yet.

See [docs/architecture.md](docs/architecture.md) for the intended fail-closed design and missing integration work.

## Local development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
python -m unittest discover -s tests -v
```

For a connection test, create a root-only configuration file using `config/duo.example.ini` and run:

```bash
proxmox-duo --config /path/to/duo.ini check
```

To send an actual Duo Push to a pre-enrolled user, explicitly execute:

```bash
proxmox-duo --config /path/to/duo.ini push --user root --confirm
```

The `push` command is a diagnostic, **not** a login enforcement mechanism. Do not use it as a PAM hook, authentication proxy, or session ticket issuer.

## Target environments

The first native adapter should target one explicitly identified and tested Proxmox VE release. Installation should abort on unknown versions, preserve a console recovery path, and never modify core authentication components blindly.

## License

MIT (see LICENSE).
