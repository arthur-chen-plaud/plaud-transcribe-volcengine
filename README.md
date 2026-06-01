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

## 配置

服务只从环境变量读取运行配置，不在命令行参数、代码或镜像中保存凭证。生产环境建议由部署系统、容器平台或 Secrets Manager 注入这些变量。

必需配置：

- `VOLCENGINE_API_KEY`：火山引擎 API Key。也可以不设置它，改用 `VOLCENGINE_SECRET_NAME` 从 AWS Secrets Manager 读取。

常用配置：

- `BROKER_URL`：Celery broker，默认 `redis://redis:6379/0`
- `RESULT_BACKEND`：Celery result backend，默认 `redis://redis:6379/0`
- `TASK_NAME`：Celery 任务名，默认 `plaud-transcribe-volcengine`
- `QUEUE_NAME`：Celery 队列名，默认同 `TASK_NAME`
- `WORKER_NAME`：worker 节点名，默认使用 hostname
- `MAX_NUM_SEQS`：worker 并发数，默认 `128`
- `VOLCENGINE_RESOURCE_ID`：默认 `volc.bigasr.auc`
- `VOLCENGINE_DEFAULT_AUDIO_FORMAT`：可选；默认从 URL 后缀推断
- `VOLCENGINE_SSD_VERSION`：开启说话人分离时使用，默认 `200`
- `VOLCENGINE_QUERY_TIMEOUT`：默认 `540` 秒
- `VOLCENGINE_POLL_INTERVAL`：默认 `5` 秒
- `VOLCENGINE_SUBMIT_RETRY_DELAYS`：submit 重试间隔，默认 `0,2,10`
- `VOLCENGINE_WARMUP_URL`：可选，配置后启动时提交一次 warmup 音频

兼容配置：

- `VOLCENGINE_APP_KEY` / `VOLCENGINE_ACCESS_KEY`：旧版控制台 App Key / Access Key，有 `VOLCENGINE_API_KEY` 时优先使用 API Key。
- `VOLCENGINE_SECRET_NAME`：可选，配置后从 AWS Secrets Manager 读取凭证。
- `AWS_REGION`、`AWS_ACCESS_KEY_ID`、`AWS_SECRET_ACCESS_KEY`：访问 AWS Secrets Manager 所需配置；未显式设置 AK/SK 时，SDK 使用默认凭证链。

单个转写任务的 submit 和 query 会复用同一组火山凭证；如果 Secrets Manager 配置多组凭证，worker 只在不同任务之间轮转凭证。

Secrets Manager 内容支持对象或对象数组，字段名支持：

```json
{
  "name": "primary",
  "api_key": "your-api-key"
}
```

或旧版 App Key 格式：

```json
{
  "name": "primary",
  "app_key": "your-app-key",
  "access_key": "your-access-key"
}
```

## Docker 启动

```bash
docker build -t celery_volcengine:latest .
```

运行前由当前 shell、部署系统或容器平台提供环境变量，然后执行：

```bash
./start_docker.sh
```

脚本只会把宿主机当前环境中已经设置的变量转发到容器；Docker 不会自动继承宿主机所有环境变量，也不会和宿主机环境变量互相污染。

## 本地开发

本地开发也使用环境变量。确认 Redis、火山凭证等变量已经在当前 shell 中存在后，可以直接启动：

```bash
pip install -r requirements.txt
python run_celery.py
```
