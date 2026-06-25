import os
from typing import override

import structlog
from django.apps import AppConfig

logger = structlog.stdlib.get_logger("reclaimer_central.system")


class SystemConfig(AppConfig):
    name: str = "system"

    @override
    def ready(self):
        from shared.opensearch import OpenSearchLogClient

        opensearch_url = os.environ.get(
            "OPENSEARCH_URL", "http://localhost:9200"
        )
        client = OpenSearchLogClient(opensearch_url=opensearch_url)
        try:
            client.setup_retention_policy()
        except Exception:
            logger.exception("Unknown exception occurred.")
            # OpenSearch may not be ready yet; gunicorn workers will retry
