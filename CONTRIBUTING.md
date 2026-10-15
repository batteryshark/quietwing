# Contributing

Read [architecture](docs/architecture.md) and [status](docs/status.md). OS desktop
management belongs in QuietWing; harness tools and image/OCR handling belong in
computer-ctrl. The interface is [CONTRACT.md](CONTRACT.md).

## Checks

Python 3.11+ runs portable tests without desktop tools or native builds:

```sh
python scripts/check.py
```

Build and inspect distributions:

```sh
python -m pip install build
python -m build
python scripts/check_distribution.py dist
```

Install the wheel in a fresh environment outside the checkout, then run
`python scripts/check_installed.py /path/to/fresh-env/bin/python`. Windows uses
`fresh-env\Scripts\python.exe`. The check verifies resources and CLI identity
without starting a desktop or probing settings.

Hosted CI runs fake-adapter and transport checks, not real GUI acceptance. Run
native tests only on an explicitly available target following
[ACCEPTANCE.md](ACCEPTANCE.md). Backend behavior changes require affected native
acceptance and two real harness workflows. Keep raw evidence private and record
a portable summary. A compiler/test-runner exit alone is insufficient.

## Changes

Use focused branches and describe the trigger, resulting behavior, and validation.
Add regression tests for identity, generation, literal arguments, and cleanup.
Default checks must never start desktops, request permissions, or change host
settings. Keep credentials, disks, snapshots, inventories, and machine captures
out of commits and packages. Use synthetic images for tests.

Bug reports should include redacted commands/error codes, OS/Python version, and
whether the session was new or resumed. Security reports follow
[SECURITY.md](SECURITY.md).
