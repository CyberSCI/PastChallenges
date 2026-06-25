import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

import jsonpath
import structlog
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk

logger = structlog.stdlib.get_logger("reclaimer_central.shared")


@dataclass
class OpenSearchResponse:
    records: list[dict[str, object]]
    total_hits: dict[str, object]

    def __init__(
        self,
        records: list[dict[str, str | int | dict[str, object]]],
        total_hits: dict[str, object],
    ) -> None:
        self.records = []
        for record in records:
            flattened_record: dict[str, object] = {}
            src_data = record.pop("_source")
            for key, value in record.items():
                flattened_record[key] = value
            assert isinstance(src_data, dict)
            for key, value in src_data.items():
                flattened_record[key] = value
            self.records.append(flattened_record)
        self.total_hits = total_hits

    @property
    def page_size(self):
        return len(self.records)

    @classmethod
    def default(cls, obj: object):
        if isinstance(obj, OpenSearchResponse):
            return {
                "records": obj.records,
                "total_hits": obj.total_hits,
                "page_size": obj.page_size,
            }
        raise TypeError


class OpenSearchLogClient:
    def __init__(
        self,
        index_prefix: str = "django-logs",
        opensearch_url: str = "http://localhost:9200",
        timeout: int = 5,
    ) -> None:
        self._index_prefix: str = index_prefix
        self._client: OpenSearch = OpenSearch(
            hosts=[opensearch_url],
            use_ssl=opensearch_url.startswith("https"),
            verify_certs=False,
            timeout=timeout,
            max_retries=1,
            retry_on_timeout=False,
        )

    def send_log(self, record: logging.LogRecord):
        doc = self._build_document(record)
        self._client.index(
            index=self._index_name(),
            body=doc,
        )

    def send_logs_bulk(self, records: list[logging.LogRecord]):
        if not records:
            return
        index = self._index_name()
        actions = [
            {"_index": index, "_source": self._build_document(r)}
            for r in records
        ]
        bulk(self._client, actions, raise_on_error=False)

    def get_logs(
        self,
        level: Literal["warning"]
        | Literal["error"]
        | Literal["info"]
        | Literal["debug"]
        | None = None,
        size: int = 50,
        request_id: str | None = None,
        username: str | None = None,
    ):
        filters: list[dict[str, object]] = []
        if level is not None:
            filters.append({"term": {"level": level}})
        if request_id is not None:
            filters.append({"term": {"request_id.keyword": request_id}})
        if username is not None:
            filters.append({"term": {"username.keyword": username}})

        query = {
            "query": {
                "bool": {
                    "must": filters,
                },
            },
            "size": size,
        }

        results = self._client.search(
            body=query,
            index=f"{self._index_prefix}-*",
            sort="timestamp:desc",  # pyright: ignore
        )
        hits = jsonpath.findall("$.hits.hits[*]", results)
        total_hits = jsonpath.findall("$.hits.total", results)[0]

        return OpenSearchResponse(records=hits, total_hits=total_hits)  # pyright: ignore

    def setup_retention_policy(self, max_index_age: str = "1d") -> None:
        """
        Create or update ISM policy to delete log indices after max_index_age.
        """
        policy_id = f"{self._index_prefix}-retention"
        policy_body = {
            "policy": {
                "description": f"Delete {self._index_prefix}-* indices after {max_index_age}",
                "default_state": "hot",
                "states": [
                    {
                        "name": "hot",
                        "transitions": [
                            {
                                "state_name": "delete",
                                "conditions": {"min_index_age": max_index_age},
                            }
                        ],
                    },
                    {
                        "name": "delete",
                        "actions": [{"delete": {}}],
                        "transitions": [],
                    },
                ],
                "ism_template": [
                    {
                        "index_patterns": [f"{self._index_prefix}-*"],
                        "priority": 100,
                    }
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

        logger.info(
            "Configured OpenSearch retention policy.",
            policy_id=policy_id,
            max_age=max_index_age,
        )

    def _index_name(self):
        return (
            f"{self._index_prefix}-{datetime.now(tz=UTC).strftime('%Y.%m.%d')}"
        )

    def _build_document(self, record: logging.LogRecord) -> dict[str, str]:
        doc: dict[str, str] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=UTC
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event_raw": record.getMessage(),
        }

        # add msg items to record

        for key, value in record.msg.items():  # pyright: ignore
            try:
                json.dumps(value)
                doc.update({key: value})
            except (json.JSONDecodeError, TypeError):
                doc.update({key: str(value)})

        return doc
