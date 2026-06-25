# OpenSearch Log Retention Policy (24h ISM)

## Overview
Add ISM (Index State Management) policy to auto-delete `django-logs-*` indices after 24 hours. Runs idempotently on every Django startup.

## Changes

### 1. `shared/opensearch.py` — Add `setup_retention_policy()` to `OpenSearchLogClient`

Add this method to the `OpenSearchLogClient` class:

```python
def setup_retention_policy(self, max_index_age: str = "1d") -> None:
    """Create or update ISM policy to delete log indices after max_index_age."""
    policy_id = f"{self._index_prefix}-retention"
    policy_body = {
        "policy": {
            "description": f"Delete {self._index_prefix}-* indices after {max_index_age}",
            "default_state": "hot",
            "states": [
                {
                    "name": "hot",
                    "transitions": [
                        {"state_name": "delete", "conditions": {"min_index_age": max_index_age}}
                    ],
                },
                {
                    "name": "delete",
                    "actions": [{"delete": {}}],
                    "transitions": [],
                },
            ],
            "ism_template": [
                {"index_patterns": [f"{self._index_prefix}-*"], "priority": 100}
            ],
        }
    }

    try:
        existing = self._client.transport.perform_request(
            "GET", f"/_plugins/_ism/policies/{policy_id}"
        )
        seq_no = existing["_seq_no"]
        primary_term = existing["_primary_term"]
        self._client.transport.perform_request(
            "PUT",
            f"/_plugins/_ism/policies/{policy_id}?if_seq_no={seq_no}&if_primary_term={primary_term}",
            body=policy_body,
        )
    except Exception:
        self._client.transport.perform_request(
            "PUT", f"/_plugins/_ism/policies/{policy_id}", body=policy_body
        )

    logger.info("opensearch_retention_policy_configured", policy_id=policy_id, max_age=max_index_age)
```

Key design decisions:
- `ism_template` auto-attaches policy to new indices matching `django-logs-*`
- Idempotent: GET existing policy → update with seq_no/primary_term for optimistic concurrency, or create if not found
- Two states: `hot` (active logging) → `delete` (triggered after 24h via `min_index_age: "1d"`)

### 2. `system/apps.py` — Call retention policy setup on Django startup

Replace entire file with:

```python
import os

from django.apps import AppConfig


class SystemConfig(AppConfig):
    name = 'system'

    def ready(self):
        from shared.opensearch import OpenSearchLogClient

        opensearch_url = os.environ.get("OPENSEARCH_URL", "http://localhost:9200")
        client = OpenSearchLogClient(opensearch_url=opensearch_url)
        try:
            client.setup_retention_policy()
        except Exception:
            pass  # OpenSearch may not be ready yet; gunicorn workers will retry
```

Notes:
- `ready()` runs once per gunicorn worker. ISM PUT is idempotent so concurrent calls are safe.
- Wrapped in try/except because OpenSearch may be unavailable during migrations or test runs.
- Uses `OPENSEARCH_URL` env var (already set in `devenv.nix`).
