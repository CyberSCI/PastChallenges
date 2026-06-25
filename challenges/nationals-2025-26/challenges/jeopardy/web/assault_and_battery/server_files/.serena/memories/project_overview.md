# Assault and Battery - Project Overview

## Purpose
"Assault and Battery" is a **CTF (Capture The Flag) jeopardy web challenge** for CyberSci 2026 NTL. It is a Django REST API server called "Reclaimer Central" that features a custom password hashing scheme. The challenge likely revolves around security vulnerabilities in the custom `ReclaimerPasswordHasher` (which uses MD5 + pepper "reinforcement" before Argon2 hashing, and logs sensitive data).

## Backstory / Theme
- Themed as an internal comms/bulletin server for "Reclaimers"
- Author: Robert Babaev
- The fictional developer was forced to use cheap Argon2 settings by "Overseer XA-12"

## Tech Stack
- **Language**: Python 3.13
- **Framework**: Django 6.0.2
- **API**: Django REST Framework 3.16.1
- **Authentication**: django-rest-knox 5.0.2 (token-based auth)
- **Password Hashing**: Custom hasher using argon2-cffi with MD5 "reinforcement" and a pepper
- **Logging**: django-structlog 10.0.0, opensearch-py (ships logs to OpenSearch)
- **Database**: SQLite3
- **Dev Environment**: devenv (Nix-based) with uv for Python package management
- **Testing**: pytest + pytest-django

## Key Security Notes (Challenge-Relevant)
1. The custom hasher (`authentication/hasher.py`) logs the intermediate hash data at DEBUG level, including the hash and data being compared
2. Uses MD5 for "reinforcement" — a known weak hash
3. Uses `argon2.profiles.CHEAPEST` — weakest Argon2 profile
4. Default pepper is hardcoded: `"jason-is-a-dingus"`
5. Logs are written to `logs/json.log` and `logs/flat_line.log`
