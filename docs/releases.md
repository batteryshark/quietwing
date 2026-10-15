# Releases

QuietWing uses a manually reviewed release process. No workflow uploads to PyPI.
The repository/package are `quietwing`; the CLI has the same single name.

## Prepare

1. Update the version in `pyproject.toml`, `__init__.py`, and `cli.py`; portable
   checks enforce agreement. Update README/status and the changelog.
2. Run `python scripts/check.py`, build fresh archives with `python -m build`,
   and run `python scripts/check_distribution.py dist`. Use an empty output
   directory so older packages cannot be mistaken for the release.
3. Install the wheel in a fresh environment outside the checkout and run
   `python scripts/check_installed.py /path/to/fresh-env/bin/python`.
4. Rebuild a wheel from the source archive and run the installed check again.
   Both archives must carry the license, required resources, and guides while
   excluding credentials, evidence, VM storage, generated binaries, and caches.
5. Inspect the Git diff and history before first publication. Existing 0.2
   native reports are historical; add current native evidence for changed
   backend behavior. State unavailable-target deferrals explicitly.

## GitHub repositories

The public MIT project is [batteryshark/quietwing](https://github.com/batteryshark/quietwing).
Computer-ctrl consumes the versioned executable interface; its integration is
[merged separately](https://github.com/batteryshark/computer-ctrl/pull/1).
Private vulnerability reporting is enabled. Keep local state/evidence ignored.

Hosted CI runs portable tests and clean package checks on Linux, Mac, and Windows.
It does not provide an authenticated native child or provisioned guest. Current
release/native coverage is documented in [status](status.md).

## Draft a versioned release

Push a reviewed `vVERSION` tag, then manually run the **Draft release** workflow
for that exact tag. It verifies the tag/version agreement, repeats portable
checks, builds/audits archives, and creates a draft GitHub release containing
the wheel, source archive, and SHA256SUMS. It does not publish the draft.
Review the generated notes and capability limits before publishing it.

The workflow checks out the supplied tag, not an unrelated current branch.
Its release job has `contents: write`; ordinary CI has read-only permissions.
No cloud credentials or package-registry tokens are required.

Publish the reviewed draft explicitly with `gh release edit vVERSION --draft=false`.
Then verify the public assets against SHA256SUMS and smoke-test the downloaded
wheel. Publishing requires the maintainer's authorization; it is not an automatic
side effect of pushing a branch.
