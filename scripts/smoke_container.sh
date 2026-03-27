#!/usr/bin/env bash
set -euo pipefail

image_tag="${1:?usage: smoke_container.sh <image-tag>}"
port="${PORT:-18086}"
container_id=""

cleanup() {
  if [[ -n "${container_id}" ]]; then
    docker rm -f "${container_id}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

container_id="$(docker run -d --rm \
  -p "127.0.0.1:${port}:8080" \
  -e AI_RUNTIME_LLM_PROVIDER=stub \
  "${image_tag}")"

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${port}/healthz" >/tmp/ai-runtime-health.json 2>/dev/null; then
    break
  fi
  sleep 1
done

health_payload="$(curl -fsS "http://127.0.0.1:${port}/healthz")"
python3 -c 'import json, sys; payload=json.loads(sys.argv[1]); assert payload["status"] == "ok", payload' "${health_payload}"

turn_payload="$(curl -fsS \
  -X POST "http://127.0.0.1:${port}/v1/runtime/turn" \
  -H 'content-type: application/json' \
  -d '{"session_id":"ci-smoke-session","user_message":"What is the first product target?"}')"
python3 -c 'import json, sys; payload=json.loads(sys.argv[1]); assert payload["response_text"], payload; assert payload["citations_used"] >= 1, payload' "${turn_payload}"
