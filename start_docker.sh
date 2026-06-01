#!/usr/bin/env bash
set -euo pipefail

ENV_NAMES=(
    BROKER_URL
    RESULT_BACKEND
    TASK_NAME
    QUEUE_NAME
    WORKER_NAME
    HEALTH_PORT
    VERSION
    LOG_TO_FILE
    MAX_NUM_SEQS
    VOLCENGINE_API_KEY
    VOLCENGINE_APP_KEY
    VOLCENGINE_ACCESS_KEY
    VOLCENGINE_SECRET_NAME
    VOLCENGINE_RESOURCE_ID
    VOLCENGINE_DEFAULT_AUDIO_FORMAT
    VOLCENGINE_MODEL_NAME
    VOLCENGINE_MODEL_VERSION
    VOLCENGINE_SSD_VERSION
    VOLCENGINE_QUERY_TIMEOUT
    VOLCENGINE_POLL_INTERVAL
    VOLCENGINE_HTTP_TIMEOUT
    VOLCENGINE_SUBMIT_RETRY_DELAYS
    VOLCENGINE_WARMUP_URL
    AWS_REGION
    AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY
)

ENV_ARGS=()
for name in "${ENV_NAMES[@]}"; do
    if [[ -n "${!name:-}" ]]; then
        ENV_ARGS+=("-e" "${name}")
    fi
done

docker run --restart=on-failure:3 \
    -itd \
    --network=plaud \
    -p 8082:8080 \
    "${ENV_ARGS[@]}" \
    --name cele_volcengine \
    celery_volcengine:latest
