# QuietWing

Before changing code, read `CONTRIBUTING.md` and `CONTRACT.md`. For adapter
changes, read that platform's README and setup guide. The descriptor schema is
`session.schema.json`; the current support/validation limits are `docs/status.md`.

Run `python scripts/check.py` for portable checks. They must not acquire a desktop
or change settings. Build/install validation follows `docs/releases.md`. Native
behavior changes additionally require real acceptance and two harness workflows
on each affected, explicitly available platform; record deferrals honestly.

Preserve generation checks, literal argv/text, owned-resource cleanup, private
state, and refusal to target the human desktop. Keep session/provisioning work
here; computer-ctrl consumes the versioned CLI without importing this source.
The sole package/import/command name is `quietwing`; add no legacy aliases.

Retain existing native state/cache identities. Keep credentials, VM storage,
snapshots, machine inventories and private captures out of Git and packages.
Keep public behavior and limits current in the linked guides and `docs/status.md`.
Keep private operational evidence and handoff records outside the product tree.
