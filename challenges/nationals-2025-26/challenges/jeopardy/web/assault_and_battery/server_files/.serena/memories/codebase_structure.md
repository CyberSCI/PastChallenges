# Codebase Structure

```
server_files/                      # Project root
├── manage.py                      # Django management script
├── pyproject.toml                 # Project config, dependencies, ruff/pyright/pytest config
├── conftest.py                    # Root pytest configuration (configures Django settings for tests)
├── devenv.nix                     # Nix dev environment config
├── devenv.yaml                    # Nix devenv inputs
├── NOTES.md                       # Backstory notes
├── test-plan.md                   # Test plan documentation
├── db.sqlite3                     # SQLite database (gitignored)
├── logs/                          # Log output directory (gitignored)
│
├── reclaimer_central/             # Django project (settings, root URLs)
│   ├── __init__.py
│   ├── settings.py                # Django settings (includes structlog, REST framework, Argon2 config)
│   ├── urls.py                    # Root URL config: admin/ and api/auth/
│   ├── log_handlers.py            # OpenSearchHandler — ships logs to OpenSearch
│   ├── asgi.py                    # ASGI entrypoint
│   └── wsgi.py                    # WSGI entrypoint
│
└── authentication/                # Django app for authentication
    ├── __init__.py
    ├── apps.py                    # App config
    ├── admin.py                   # Admin registration (empty)
    ├── models.py                  # Models (empty — uses default Django User)
    ├── views.py                   # LoginView (extends knox LoginView)
    ├── urls.py                    # Routes: login/, logout/, logoutall/
    ├── hasher.py                  # ReclaimerPasswordHasher (custom Argon2 + MD5 + pepper)
    ├── tests.py                   # pytest test suite for the hasher
    └── migrations/
        └── __init__.py
```

## API Endpoints
- `POST /api/auth/login/` — Login (returns knox token)
- `POST /api/auth/logout/` — Logout (invalidates token)
- `POST /api/auth/logoutall/` — Logout all sessions

## Key Files
- `authentication/hasher.py` — The core of the challenge; custom password hasher
- `reclaimer_central/settings.py` — Django configuration, logging setup, REST framework config
- `authentication/views.py` — Login view using Knox
- `authentication/tests.py` — Test suite for `ReclaimerPasswordHasher`
