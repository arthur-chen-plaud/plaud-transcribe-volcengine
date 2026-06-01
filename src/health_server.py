import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from loguru import logger

from config import TASK_NAME, VERSION, WORKER_NAME


thread = None


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return

        data = {
            "status": 0,
            "message": "success",
            "data": {
                "health_status": "ok",
                "timestamp": int(time.time()),
                "service": TASK_NAME,
                "worker": WORKER_NAME,
                "version": VERSION,
            },
        }
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_health_server(port=8080):
    global thread
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.pid = os.getpid()
    logger.info(f"[HealthCheck] PID={server.pid} listening on {server.server_address[1]}")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()


if __name__ == "__main__":
    start_health_server()
    thread.join()
