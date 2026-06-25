import http
import json
from typing import Any

import orjson
import structlog
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.opensearch import OpenSearchLogClient, OpenSearchResponse
from shared.views import AuthenticatedApiView

logger = structlog.stdlib.get_logger("reclaimer_central.system")


class HealthView(APIView):
    def get(self, request: Request, format=None):
        """
        Get system health
        """

        response_data = {"status": "ok"}

        return Response(response_data)


class LogsView(AuthenticatedApiView):
    def get(self, request: Request, format=None):
        log_client = OpenSearchLogClient()

        query_params: dict[str, Any] = request.query_params

        size = int(query_params.get("size", 50))
        match query_params.get("level"):
            case "warning":
                level = "warning"
            case "info":
                level = "info"
            case "error":
                level = "error"
            case "debug":
                level = "debug"
            case None:
                level = None
            case _:
                return Response(
                    {"message": "Invalid log level."},
                    status=http.HTTPStatus.BAD_REQUEST,
                )

        request_id = query_params.get("request_id")
        username = query_params.get("username")

        log_data = log_client.get_logs(
            level=level, size=size, request_id=request_id, username=username
        )
        response_data = json.loads(
            orjson.dumps(
                log_data,
                option=orjson.OPT_PASSTHROUGH_DATACLASS,
                default=OpenSearchResponse.default,
            )
        )

        return Response(response_data)
