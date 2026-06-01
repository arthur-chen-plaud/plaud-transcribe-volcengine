import json
import time
from urllib.parse import urlparse

import requests
from loguru import logger

from config import (
    VOLCENGINE_DEFAULT_AUDIO_FORMAT,
    VOLCENGINE_HTTP_TIMEOUT,
    VOLCENGINE_MODEL_NAME,
    VOLCENGINE_MODEL_VERSION,
    VOLCENGINE_POLL_INTERVAL,
    VOLCENGINE_QUERY_TIMEOUT,
    VOLCENGINE_QUERY_URL,
    VOLCENGINE_RESOURCE_ID,
    VOLCENGINE_SSD_VERSION,
    VOLCENGINE_SUBMIT_URL,
    VOLCENGINE_WARMUP_URL,
)
from src.datas import TranscribeRequest, TranscribeResponse
from src.secret_keys import get_volcengine_credentials


SUCCESS_CODE = "20000000"
PENDING_CODES = {"20000001", "20000002"}
SUPPORTED_AUDIO_FORMATS = {"raw", "wav", "mp3", "ogg", "m4a", "flac", "aac", "amr", "pcm"}


def _header_value(response, key):
    return response.headers.get(key) or response.headers.get(key.lower()) or ""


def _status(response):
    return _header_value(response, "X-Api-Status-Code")


def _message(response):
    return _header_value(response, "X-Api-Message")


def _logid(response):
    return _header_value(response, "X-Tt-Logid")


def _build_headers(task_id, credentials, include_sequence=True, logid=""):
    headers = {
        "Content-Type": "application/json",
        "X-Api-Resource-Id": VOLCENGINE_RESOURCE_ID,
        "X-Api-Request-Id": str(task_id),
    }
    if include_sequence:
        headers["X-Api-Sequence"] = "-1"
    if logid:
        headers["X-Tt-Logid"] = logid

    if credentials.get("api_key"):
        headers["X-Api-Key"] = credentials["api_key"]
    else:
        headers["X-Api-App-Key"] = credentials["app_key"]
        headers["X-Api-Access-Key"] = credentials["access_key"]
    return headers


def _build_corpus(req):
    if req.phrases:
        return {
            "context": json.dumps(
                {"hotwords": [{"word": phrase} for phrase in req.phrases]},
                ensure_ascii=False,
            )
        }
    if req.request_prompt:
        return {
            "context": json.dumps(
                {
                    "context_type": "dialog_ctx",
                    "context_data": [{"text": req.request_prompt}],
                },
                ensure_ascii=False,
            )
        }
    return None


def _build_request(req, credentials):
    uid = credentials.get("app_key") or credentials.get("api_key") or "volcengine-asr"
    audio = {"url": req.file_url}
    audio_format = _infer_audio_format(req.file_url)
    if audio_format:
        audio["format"] = audio_format
    if req.language and req.language != "auto":
        audio["language"] = req.language

    request = {
        "user": {"uid": uid},
        "audio": audio,
        "request": {
            "model_name": VOLCENGINE_MODEL_NAME,
            "enable_itn": True,
            "enable_punc": True,
            "enable_ddc": True,
            "show_utterances": True,
            "enable_speaker_info": req.diarization,
        },
    }
    if VOLCENGINE_MODEL_VERSION:
        request["request"]["model_version"] = VOLCENGINE_MODEL_VERSION
    if req.diarization and VOLCENGINE_SSD_VERSION:
        request["request"]["ssd_version"] = VOLCENGINE_SSD_VERSION

    corpus = _build_corpus(req)
    if corpus:
        request["request"]["corpus"] = corpus
    return request


def _infer_audio_format(file_url):
    if VOLCENGINE_DEFAULT_AUDIO_FORMAT:
        return VOLCENGINE_DEFAULT_AUDIO_FORMAT

    suffix = urlparse(file_url).path.rsplit(".", 1)
    if len(suffix) != 2:
        return ""
    audio_format = suffix[1].lower()
    if audio_format == "opus":
        return "ogg"
    if audio_format in SUPPORTED_AUDIO_FORMATS:
        return audio_format
    return ""


def submit_task(task_id, req):
    credentials = get_volcengine_credentials()
    if credentials is None:
        logger.error(f"Failed to get volcengine credentials, task_id: {task_id}")
        return None

    headers = _build_headers(task_id, credentials, include_sequence=True)
    body = _build_request(req, credentials)
    try:
        response = requests.post(
            VOLCENGINE_SUBMIT_URL,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            timeout=VOLCENGINE_HTTP_TIMEOUT,
        )
    except Exception as e:
        logger.error(f"volcengine submit error: {e}, task_id: {task_id}")
        return None

    code = _status(response)
    if code == SUCCESS_CODE:
        logid = _logid(response)
        logger.info(f"volcengine submit success, task_id: {task_id}, logid: {logid}")
        return logid

    logger.error(
        f"volcengine submit failed, task_id: {task_id}, code: {code}, "
        f"message: {_message(response)}, response: {response.text}"
    )
    return None


def query_task(task_id, logid):
    credentials = get_volcengine_credentials()
    if credentials is None:
        logger.error(f"Failed to get volcengine credentials, task_id: {task_id}")
        return None, "credential_error"

    headers = _build_headers(task_id, credentials, include_sequence=False, logid=logid)
    deadline = time.time() + VOLCENGINE_QUERY_TIMEOUT
    while time.time() < deadline:
        try:
            response = requests.post(
                VOLCENGINE_QUERY_URL,
                data=b"{}",
                headers=headers,
                timeout=VOLCENGINE_HTTP_TIMEOUT,
            )
        except Exception as e:
            logger.error(f"volcengine query error: {e}, task_id: {task_id}")
            time.sleep(VOLCENGINE_POLL_INTERVAL)
            continue

        code = _status(response)
        logger.info(
            f"volcengine query, task_id: {task_id}, code: {code}, "
            f"message: {_message(response)}, logid: {_logid(response)}"
        )
        if code == SUCCESS_CODE:
            try:
                return response.json(), "success"
            except json.JSONDecodeError as e:
                logger.error(f"volcengine query json parse error: {e}, task_id: {task_id}")
                return None, "json_error"
        if code not in PENDING_CODES:
            logger.error(
                f"volcengine query failed, task_id: {task_id}, code: {code}, "
                f"message: {_message(response)}, response: {response.text}"
            )
            return None, f"volcengine_error_{code or 'unknown'}"

        time.sleep(VOLCENGINE_POLL_INTERVAL)

    logger.error(f"volcengine query timeout, task_id: {task_id}")
    return None, "volcengine_timeout"


def _duration_ms(audio_info):
    try:
        return int(audio_info.get("duration") or 0)
    except (TypeError, ValueError):
        return 0


def convert_volcengine_response(res):
    result = res.get("result") or {}
    if isinstance(result, list):
        result = result[0] if result else {}

    utterances = result.get("utterances") or []
    if not utterances and result.get("text"):
        return [
            {
                "text": result["text"],
                "offset": 0,
                "duration": _duration_ms(res.get("audio_info") or {}),
                "words": [],
            }
        ]

    segments = []
    for utterance in utterances:
        start = int(utterance.get("start_time") or 0)
        end = int(utterance.get("end_time") or start)
        words = []
        for word in utterance.get("words") or []:
            word_start = int(word.get("start_time") or 0)
            word_end = int(word.get("end_time") or word_start)
            words.append(
                {
                    "text": word.get("text", ""),
                    "offset": word_start,
                    "duration": max(word_end - word_start, 0),
                }
            )

        segment = {
            "text": utterance.get("text", ""),
            "offset": start,
            "duration": max(end - start, 0),
            "words": words,
        }
        speaker = utterance.get("speaker") or utterance.get("speaker_id")
        additions = utterance.get("additions") or {}
        speaker = speaker or additions.get("speaker") or additions.get("speaker_id")
        if speaker is not None:
            try:
                segment["speaker"] = f"SPEAKER_{int(speaker):02d}"
            except (TypeError, ValueError):
                segment["speaker"] = str(speaker)
        if utterance.get("channel_id") is not None:
            segment["channel_id"] = utterance["channel_id"]
        segments.append(segment)
    return segments


def warmUp():
    if not VOLCENGINE_WARMUP_URL:
        logger.info("volcengine warmUp skipped, VOLCENGINE_WARMUP_URL is empty")
        return

    logger.info("volcengine warmUp start")
    req = TranscribeRequest(file_url=VOLCENGINE_WARMUP_URL, language="auto")
    res = trans_req("warmup", req)
    if res.status == "success":
        logger.info("volcengine warmUp success")
    else:
        logger.error(f"volcengine warmUp failed, status: {res.status}")


def trans_req(task_id, req: TranscribeRequest):
    logger.info(f"volcengine trans_req start, task_id: {task_id}, file_url: {req.file_url}")
    logid = submit_task(task_id, req)
    if not logid:
        return TranscribeResponse(status="volcengine_submit_error", segments=[])

    res, status = query_task(task_id, logid)
    if status != "success" or res is None:
        return TranscribeResponse(status=status, segments=[])

    logger.info(f"volcengine trans_req end, task_id: {task_id}")
    return TranscribeResponse(status="success", segments=convert_volcengine_response(res))
