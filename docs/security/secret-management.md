# Secret Management

## Policy

- Do not commit plaintext secrets.
- Do not place secrets in Markdown, screenshots, prompts, handover files, or comments.
- Store real values in Doppler.
- Keep local values in `.env`.
- Treat any previously exposed value as compromised.
- Rotate exposed values before continuing deployment or automation work.

## Git Ignore Requirements

The repo must ignore:

```gitignore
.env
.env.*
!.env.example
.secrets/
ROTATE.md
HANDOVER.old.md
```

`.env.example` must list variable names only. It must not include local passwords, tokens, API keys, webhook secrets, SMTP credentials, or usable URLs with credentials.

## Doppler Placeholder Format

When a value is removed from docs or memory files, replace it with:

```text
<SECRET:NAME_IN_DOPPLER>
```

Add this note near the redaction:

```text
Secret value removed. Store and rotate in Doppler. Treat previous value as compromised.
```

Do not move the old value into another Markdown file. Do not preserve old values in comments.

## Install Pre-Commit And Gitleaks

Install tools:

```bash
brew install gitleaks pre-commit
```

Enable hooks in this repo:

```bash
pre-commit install
```

Run the hook manually:

```bash
pre-commit run gitleaks --all-files
```

## Local Scan Commands

Scan the full working tree:

```bash
gitleaks detect --redact --config .gitleaks.toml
```

Scan staged changes before commit:

```bash
gitleaks protect --staged --redact --config .gitleaks.toml
```

## Remediation Workflow

1. Stop and do not commit.
2. Remove the plaintext secret from the file.
3. Replace it with `<SECRET:NAME_IN_DOPPLER>`.
4. Store the real value in Doppler.
5. Rotate the exposed credential at the provider.
6. Re-run `gitleaks detect --redact --config .gitleaks.toml`.
7. Re-run `pre-commit run gitleaks --all-files`.
8. If the value entered Git history, rewrite or purge history before pushing.

## Reusable Snippet For Other Active Repos

Add `.gitleaks.toml`:

```toml
title = "Project secret scanning"

[extend]
useDefault = true

[[allowlists]]
description = "Doppler placeholder references are intentionally not secret values"
regexes = [
  '''<SECRET:[A-Z0-9_]+_IN_DOPPLER>'''
]
```

Add `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: gitleaks
        name: gitleaks
        entry: gitleaks protect --staged --redact --config .gitleaks.toml
        language: system
        pass_filenames: false
```

Add or verify `.gitignore`:

```gitignore
.env
.env.*
!.env.example
.secrets/
ROTATE.md
HANDOVER.old.md
```

Install and enable:

```bash
brew install gitleaks pre-commit
pre-commit install
gitleaks detect --redact --config .gitleaks.toml
```
