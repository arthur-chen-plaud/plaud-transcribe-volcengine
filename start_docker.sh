docker run --restart=on-failure:3 \
    -itd \
    --network=plaud \
    -p 8082:8080 \
    -e BROKER_URL="redis://redis:6379/0" \
    -e RESULT_BACKEND="redis://redis:6379/0" \
    -e TASK_NAME="plaud-transcribe-volcengine" \
    -e VOLCENGINE_API_KEY="${VOLCENGINE_API_KEY}" \
    --name cele_volcengine \
    celery_volcengine:latest
