import os


HEALTH_PORT = int(os.getenv("HEALTH_PORT", 8080))
VERSION = os.getenv("VERSION", "1.0.0")

# AWS Secrets Manager is optional. If VOLCENGINE_SECRET_NAME is empty, the
# worker reads Volcengine credentials directly from environment variables.
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
VOLCENGINE_SECRET_NAME = os.getenv("VOLCENGINE_SECRET_NAME", "")

# Celery config.
WORKER_NAME = os.getenv("WORKER_NAME", "")
TASK_NAME = os.getenv("TASK_NAME", "plaud-transcribe-volcengine")
QUEUE_NAME = os.getenv("QUEUE_NAME", TASK_NAME)
BROKER_URL = os.getenv("BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.getenv("RESULT_BACKEND", "redis://redis:6379/0")
MAX_NUM_SEQS = int(os.getenv("MAX_NUM_SEQS", 128))

# Volcengine AUC bigmodel standard API config.
VOLCENGINE_APP_KEY = os.getenv("VOLCENGINE_APP_KEY", "")
VOLCENGINE_ACCESS_KEY = os.getenv("VOLCENGINE_ACCESS_KEY", "")
VOLCENGINE_API_KEY = os.getenv("VOLCENGINE_API_KEY", "")
VOLCENGINE_RESOURCE_ID = os.getenv("VOLCENGINE_RESOURCE_ID", "volc.bigasr.auc")
VOLCENGINE_SUBMIT_URL = os.getenv(
    "VOLCENGINE_SUBMIT_URL",
    "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit",
)
VOLCENGINE_QUERY_URL = os.getenv(
    "VOLCENGINE_QUERY_URL",
    "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query",
)
VOLCENGINE_MODEL_NAME = os.getenv("VOLCENGINE_MODEL_NAME", "bigmodel")
VOLCENGINE_MODEL_VERSION = os.getenv("VOLCENGINE_MODEL_VERSION", "")
VOLCENGINE_SSD_VERSION = os.getenv("VOLCENGINE_SSD_VERSION", "200")
VOLCENGINE_DEFAULT_AUDIO_FORMAT = os.getenv("VOLCENGINE_DEFAULT_AUDIO_FORMAT", "")
VOLCENGINE_POLL_INTERVAL = float(os.getenv("VOLCENGINE_POLL_INTERVAL", 5))
VOLCENGINE_QUERY_TIMEOUT = float(os.getenv("VOLCENGINE_QUERY_TIMEOUT", 540))
VOLCENGINE_HTTP_TIMEOUT = float(os.getenv("VOLCENGINE_HTTP_TIMEOUT", 60))
VOLCENGINE_WARMUP_URL = os.getenv("VOLCENGINE_WARMUP_URL", "")
