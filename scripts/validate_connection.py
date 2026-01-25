from __future__ import annotations

import json
import os
import sys

from yueshu_airbyte_connector.common import DEFAULT_CHECK_QUERY
from yueshu_airbyte_connector.nebula_client import NebulaClient


def main() -> int:
    host = os.environ.get("YUESHU_HOST", "192.168.15.240")
    port = int(os.environ.get("YUESHU_PORT", "39669"))
    username = os.environ.get("YUESHU_USERNAME", "root")
    password = os.environ.get("YUESHU_PASSWORD", "Nebula123")
    graph = os.environ.get("YUESHU_GRAPH")
    check_query = os.environ.get("YUESHU_CHECK_QUERY", DEFAULT_CHECK_QUERY)

    client = NebulaClient(hosts=[host], port=port, username=username, password=password, graph=graph)
    try:
        client.connect()
        result = client.execute(check_query)
        payload = client.result_to_payload(result)
        sys.stdout.write(json.dumps({"status": "ok", "payload": payload}, ensure_ascii=False) + "\n")
        return 0
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"连接验证失败: {exc}\n")
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
