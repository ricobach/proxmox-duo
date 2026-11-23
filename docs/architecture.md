# Native Proxmox authentication integration plan

## Status: not implemented

The CLI only checks Duo credentials and tests Duo Push. It **does not** modify Proxmox's authentication, enable MFA, protect a web login, or issue a PVE ticket. Installing this Python package alone provides **zero extra Proxmox login security**.

## Intended authentication sequence

1. An unmodified native Proxmox authentication routine validates the `@pam` username, password, account status and other existing policy checks.
2. A supported, version-pinned server-side adapter intercepts the normal web-session ticket path *before* the final PVE session is minted, and creates a signed, short-lived provisional challenge.
3. The adapter associates the provisional challenge with the exact authenticated principal, web login context, expiration, randomized nonce, and one outstanding Duo transaction.
4. Server requests `factor=push`, `device=auto`, `async=1` via Duo Auth API. A browser status view polls only the adapter's restricted status endpoint. It never receives Duo API secrets or a raw Duo transaction ID.
5. Backend verifies Duo status, allows only a real Push approval (never bypass), and atomically consumes the one-time challenge. The existing Proxmox ticket issuance path is permitted only after successful verified Push.
6. Any Duo denial, error, timeout, missing enrollment, replay, changed user, or invalid challenge fails closed.

## Critical engineering requirements

- Research and pin exact Proxmox VE / `pve-access-control` / `proxmox-widget-toolkit` versions before changing authentication; do not guess internal APIs or monkey-patch arbitrary code.
- **Web-only is not a security boundary by itself.** Audit all paths that can obtain an equivalent PVE session: `/access/ticket`, password-based API authentication, console interfaces, alternate realms, recovery methods and API tokens. Define and enforce which ones require Duo, not just the browser button.
- Preserve existing Proxmox TFA requirements. Do not suppress or override another configured factor without an explicit, reviewed policy.
- The existing `NeedTFA` provisional ticket mechanism is a *candidate* integration point. Confirm its exact contracts on the target version; do not treat that value as a normal PVEAuthCookie.
- Challenge state must be shared across nodes or pinned to the issuing node, cryptographically bound to the principal and request, and atomically marked consumed, with rate limiting and predictable expiry.
- Use CSRF controls for state-changing endpoints, secure cookies, TLS, strict Origin checks and a browser challenge context with no session privileges.
- Make the installation opt-in, default disabled, preserve a direct console recovery procedure, and abort on unrecognized files or versions. Require upgrade compatibility checks.
- Log state transitions, never integration secrets, user passwords, Duo raw transactions, or trusted-device bypass tokens.
- An actual integration needs both positive tests and bypass tests for direct ticket creation, APIs, mismatched challenges, concurrency, cancellation, cluster hop, failed Duo responses and restart recovery.

## Why not a PAM-only implementation?

A dedicated `/etc/pam.d/proxmox-ve-auth` service can isolate PAM changes from SSH, but PAM's synchronous conversation model does not automatically provide a rich web login Push-progress experience. The intended solution uses a native backend ticket gate plus UI feedback.

## Next implementation milestone

Select a Proxmox VE release, inspect its actual `PVE/API2/AccessControl.pm`, `PVE/AccessControl.pm` and login UI source, then build and integration-test a minimal patch against a disposable lab instance. Only then add a .deb installer; no untested installer should touch a hypervisor authentication stack.

## References

- https://duo.com/docs/authapi
- https://github.com/duosecurity/duo_client_python
- https://git.proxmox.com/
