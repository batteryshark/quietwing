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

## First GitHub repository

The source is prepared for `batteryshark/quietwing`. Creating a repository,
pushing it, or publishing a release is a separate explicit action. After that
action is authorized, create the repository with the agreed visibility and
connect this existing Git history. Do not upload ignored local state/evidence.
Enable issues and private vulnerability reporting if available.

The CI workflow runs portable tests on Linux, Mac, and Windows with Python 3.11
and 3.14, and audits wheel/source packages. It runs without native desktop access,
credentials, or provisioning. Inspect actual GitHub results after the first push;
a local workflow file is not proof that remote CI passed.

## Draft a versioned release

Push a reviewed `vVERSION` tag, then manually run the **Draft release** workflow
for that exact tag. It verifies the tag/version agreement, repeats portable
checks, builds/audits archives, and creates a draft GitHub release containing
the wheel, source archive, and SHA256SUMS. It does not publish the draft.
Review the generated notes and capability limits before publishing it.

The workflow checks out the supplied tag, not an unrelated current branch.
Its release job has `contents: write`; ordinary CI has read-only permissions.
No cloud credentials or package-registry tokens are required.
