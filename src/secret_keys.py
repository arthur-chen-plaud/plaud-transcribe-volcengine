import json
import threading
import time

import boto3
from botocore.exceptions import ClientError
from loguru import logger

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    VOLCENGINE_ACCESS_KEY,
    VOLCENGINE_API_KEY,
    VOLCENGINE_APP_KEY,
    VOLCENGINE_SECRET_NAME,
)


_lock = threading.Lock()
_prev_version = ""
_idx = 0
_credentials = []


def _env_credentials():
    cred = {
        "name": "env",
        "app_key": VOLCENGINE_APP_KEY,
        "access_key": VOLCENGINE_ACCESS_KEY,
        "api_key": VOLCENGINE_API_KEY,
    }
    if cred["api_key"] or (cred["app_key"] and cred["access_key"]):
        return [cred]
    return []


def _normalize_secret(secret):
    parsed = json.loads(secret)
    items = parsed if isinstance(parsed, list) else [parsed]
    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        cred = {
            "name": item.get("name", ""),
            "app_key": (
                item.get("app_key")
                or item.get("appKey")
                or item.get("appid")
                or item.get("app_id")
                or item.get("X-Api-App-Key")
                or ""
            ),
            "access_key": (
                item.get("access_key")
                or item.get("accessKey")
                or item.get("token")
                or item.get("X-Api-Access-Key")
                or ""
            ),
            "api_key": item.get("api_key") or item.get("apiKey") or item.get("X-Api-Key") or "",
        }
        if cred["api_key"] or (cred["app_key"] and cred["access_key"]):
            normalized.append(cred)
    return normalized


def update_volcengine_credentials():
    global _credentials
    global _prev_version

    if not VOLCENGINE_SECRET_NAME:
        env_creds = _env_credentials()
        if not env_creds:
            logger.error("volcengine credentials are empty")
            return False
        with _lock:
            _credentials = env_creds
        logger.info("loaded volcengine credentials from environment")
        return True

    session = boto3.session.Session()
    client_kwargs = {
        "service_name": "secretsmanager",
        "region_name": AWS_REGION,
    }
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY
    else:
        logger.info("AWS ak/sk is empty, use default AWS credential chain")

    client = session.client(**client_kwargs)
    try:
        response = client.get_secret_value(SecretId=VOLCENGINE_SECRET_NAME)
    except ClientError as e:
        logger.error(f"update volcengine credentials error: {e}")
        return False

    version = response.get("VersionId", "")
    if version and version == _prev_version:
        logger.info(f"volcengine credentials not changed, version: {version}")
        return True

    secret = response.get("SecretString", "")
    if not secret:
        logger.error("volcengine secret is empty")
        return False

    try:
        new_credentials = _normalize_secret(secret)
    except json.JSONDecodeError as e:
        logger.error(f"volcengine secret json parse error: {e}")
        return False

    if not new_credentials:
        logger.error("volcengine secret contains no usable credentials")
        return False

    with _lock:
        _credentials = new_credentials
        _prev_version = version
    logger.info(f"update volcengine credentials, version: {version}, size={len(new_credentials)}")
    return True


def get_volcengine_credentials():
    global _idx

    with _lock:
        if not _credentials:
            return None
        _idx = (_idx + 1) % len(_credentials)
        cred = _credentials[_idx].copy()
    logger.info(f"get volcengine credentials, idx: {_idx}, name: {cred.get('name', '')}")
    return cred


def _monitor():
    while True:
        time.sleep(60)
        logger.info("load volcengine credentials in loop")
        update_volcengine_credentials()


def start_volcengine_secretmanager_monitor():
    while not update_volcengine_credentials():
        logger.error("initialize volcengine credentials failed, wait 60 seconds")
        time.sleep(60)

    thread = threading.Thread(target=_monitor, daemon=True)
    thread.start()
