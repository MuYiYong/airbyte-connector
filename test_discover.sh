#!/bin/bash
docker run --rm \
  -v "$PWD:/workspace" \
  yueshu-connector:test \
  --connector-type destination discover \
  --config /workspace/configs/destination.sample.json | python -m json.tool | head -60
