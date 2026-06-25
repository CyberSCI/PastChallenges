import pytest
from django.test import Client

from shared.opensearch import OpenSearchLogClient


@pytest.fixture(name="opensearch_client")
def fixture_opensearch_client():
    return OpenSearchLogClient()


class TestOpenSearchLogClient:
    def test_basic_log_retrieve(self, opensearch_client: OpenSearchLogClient):
        logs = opensearch_client.get_logs()
        assert int(logs.page_size) == 50

    def test_log_size(self, opensearch_client: OpenSearchLogClient):
        logs = opensearch_client.get_logs(size=25)
        assert int(logs.page_size) == 25

    def test_level_filtering(self, opensearch_client: OpenSearchLogClient):
        logs = opensearch_client.get_logs(level="info")
        for hit in logs.records:
            assert hit["level"] == "info"

    def test_request_id_filtering(
        self, opensearch_client: OpenSearchLogClient, client: Client
    ):
        test_response = client.get("/")
        logs = opensearch_client.get_logs(level="info")
        request_id = str(logs.records[-1]["request_id"])
        logs_with_request_id = opensearch_client.get_logs(request_id=request_id)
        assert int(str(logs_with_request_id.total_hits["value"])) > 0
