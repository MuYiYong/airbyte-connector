from __future__ import annotations

import os

import pytest

from yueshu_airbyte_connector.common import DEFAULT_CHECK_QUERY
from yueshu_airbyte_connector.nebula_client import NebulaClient


@pytest.mark.skipif(
    os.environ.get("YUESHU_HOST") is None,
    reason="需要设置 YUESHU_HOST/YUESHU_PORT/YUESHU_USERNAME/YUESHU_PASSWORD",
)
def test_connectivity():
    host = os.environ.get("YUESHU_HOST")
    port = int(os.environ.get("YUESHU_PORT", "39669"))
    username = os.environ.get("YUESHU_USERNAME", "root")
    password = os.environ.get("YUESHU_PASSWORD", "root")
    graph = os.environ.get("YUESHU_GRAPH")
    check_query = os.environ.get("YUESHU_CHECK_QUERY", DEFAULT_CHECK_QUERY)

    client = NebulaClient(hosts=[host], username=username, password=password, graph=graph)
    try:
        client.connect()
        result = client.execute(check_query)
        assert result is not None
    finally:
        client.close()
