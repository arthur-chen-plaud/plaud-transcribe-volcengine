# plaud-transcribe-volcengine-worker

参考 Azure Celery worker 封装的火山引擎大模型录音文件识别标准版 worker。

## 流程

1. Celery 从 Redis broker 消费 `TASK_NAME` 任务。
2. worker 调用火山引擎标准版 `submit` 接口提交音频 URL。
3. 使用同一个 `X-Api-Request-Id` 轮询 `query` 接口。
4. 将 `result.utterances` 转成与原 worker 接近的 `segments` 格式。

## 请求模型

```json
{
  "file_url": "https://example.com/audio.mp3",
  "language": "auto",
  "phrases": ["热词"],
  "request_prompt": "可选上下文",
  "diarization": false,
  "duration_seconds": 0
}
```

`language` 为 `auto` 时不传，其他值会透传到火山 `audio.language`。`phrases` 会转成热词 corpus，`request_prompt` 会在没有热词时转成上下文 corpus，`diarization` 映射到 `enable_speaker_info`。

## 主要环境变量

- `TASK_NAME`：默认 `plaud-transcribe-volcengine`
- `QUEUE_NAME`：默认同 `TASK_NAME`
- `BROKER_URL`：默认 `redis://redis:6379/0`
- `RESULT_BACKEND`：默认 `redis://redis:6379/0`
- `MAX_NUM_SEQS`：默认 `128`
- `VOLCENGINE_APP_KEY`：旧版控制台 App Key / App ID
- `VOLCENGINE_ACCESS_KEY`：旧版控制台 Access Key / Access Token
- `VOLCENGINE_API_KEY`：新版控制台 API Key，有值时优先使用
- `VOLCENGINE_RESOURCE_ID`：默认 `volc.bigasr.auc`
- `VOLCENGINE_DEFAULT_AUDIO_FORMAT`：可选；默认从 URL 后缀推断
- `VOLCENGINE_SSD_VERSION`：开启说话人分离时使用，默认 `200`
- `VOLCENGINE_SECRET_NAME`：可选，配置后从 AWS Secrets Manager 读取凭证
- `VOLCENGINE_QUERY_TIMEOUT`：默认 `540` 秒
- `VOLCENGINE_POLL_INTERVAL`：默认 `5` 秒
- `VOLCENGINE_SUBMIT_RETRY_DELAYS`：submit 重试间隔，默认 `0,2,10`
- `VOLCENGINE_WARMUP_URL`：可选，配置后启动时提交一次 warmup 音频

单个转写任务的 submit 和 query 会复用同一组火山凭证；如果 Secrets Manager 配置多组凭证，worker 只在不同任务之间轮转凭证。

Secrets Manager 内容支持对象或对象数组，字段名支持：

```json
{
  "name": "primary",
  "app_key": "your-app-key",
  "access_key": "your-access-key"
}
```

或：

```json
{
  "name": "primary",
  "api_key": "your-api-key"
}
```

## 本地启动

```bash
pip install -r requirements.txt
VOLCENGINE_APP_KEY=xxx VOLCENGINE_ACCESS_KEY=yyy python run_celery.py
```

## Docker

```bash
docker build -t celery_volcengine:latest .
docker run --rm \
  --network=plaud \
  -p 8082:8080 \
  -e BROKER_URL="redis://redis:6379/0" \
  -e RESULT_BACKEND="redis://redis:6379/0" \
  -e VOLCENGINE_APP_KEY="xxx" \
  -e VOLCENGINE_ACCESS_KEY="yyy" \
  celery_volcengine:latest
```
