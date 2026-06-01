import re
import sys

from celery.__main__ import main

from config import MAX_NUM_SEQS, WORKER_NAME


if WORKER_NAME == "":
    worker_name = "volcengine-transcribe@%h"
else:
    worker_name = "volcengine-transcribe@" + WORKER_NAME


if __name__ == "__main__":
    sys.argv = [
        "celery",
        "-A",
        "src.tasks.celery_app",
        "worker",
        "-P",
        "threads",
        "-c",
        str(MAX_NUM_SEQS),
        "--prefetch-multiplier=1",
        "--loglevel=info",
        "-n",
        worker_name,
    ]

    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    sys.exit(main())
