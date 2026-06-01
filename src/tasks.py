import time

from celery import Celery, signals
from loguru import logger

from config import BROKER_URL, HEALTH_PORT, QUEUE_NAME, RESULT_BACKEND, TASK_NAME
from src.datas import TranscribeRequest
from src.health_server import start_health_server
from src.secret_keys import start_volcengine_secretmanager_monitor
from src.volcengine import trans_req, warmUp


celery_app = Celery()
celery_app.conf.update(
    broker_url=BROKER_URL,
    result_backend=RESULT_BACKEND,
    task_default_queue=QUEUE_NAME,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_time_limit=600,
    task_soft_time_limit=540,
    broker_transport_options={
        "queue_order_strategy": "priority",
        "visibility_timeout": 600,
    },
    task_track_started=True,
)


@signals.worker_init.connect
def worker_init_handler(**kwargs):
    logger.info("volcengine worker_init signal received")
    start_health_server(port=HEALTH_PORT)
    start_volcengine_secretmanager_monitor()
    warmUp()
    logger.info("volcengine worker_init signal end")


@celery_app.task(bind=True, name=TASK_NAME, pydantic=True)
def transcribe(self, args: TranscribeRequest):
    try:
        created_at_ms = 0
        if self.request.headers is not None:
            created_at_ms = self.request.headers.get("created_at", 0)

        started_at = time.time()
        res = trans_req(self.request.id, args)
        delay = round(started_at - created_at_ms / 1000, 3)
        if delay < 0:
            delay = 0
        res.delay = delay
        res.spend = round(time.time() - started_at, 3)
        res.nodename = self.request.hostname
        logger.info(
            f"request_id: {self.request.id} nodename: {res.nodename} "
            f"delay: {res.delay} spend: {res.spend}"
        )
        if res.status == "success":
            return res.model_dump()

        self.update_state(
            state="FAILURE",
            meta={"exc_type": "ValueError", "exc_message": res.status},
        )
        return res.model_dump()
    except Exception:
        self.app.control.shutdown(destination=[self.request.hostname])
        raise
