# Quickstart: research validation

All checks below run locally and offline. They do not contact Wallex or use credentials.

## Prerequisites

- Python 3.11 or newer
- Git
- For Spec Kit workflow authoring: pinned official Spec Kit 1.2.2 CLI (`specify`); installation and integration are recorded in [spec-kit-setup.md](spec-kit-setup.md).

## Validate the source register and internal links

From the repository root:

```bash
python3 scripts/validate_sources.py
python3 scripts/validate_doc_links.py
git diff --check
```

The first checks source-register structure, provenance, unique source IDs/URLs, UTC timestamps, allowed state labels, and related-ID references. The second checks only relative Markdown links that resolve to local files; external network links are not tested or rewritten.

## Spec Kit checks

When the CLI is installed:

```bash
specify version
specify --help
specify integration list
```

`specify integration list` is project-scoped and must be run inside this repository. The `generic` integration provides generated skill instructions; Arena slash-command invocation is not claimed.

## Research safety

Do not add a real `.env`, API key, cookie, account identifier, or private user data. Do not run endpoint examples, test production WebSockets, or execute any trade/cancellation/transfer. For source updates, read [CONTRIBUTING.md](../../CONTRIBUTING.md) and update the source register, matrix, and affected summaries together.
