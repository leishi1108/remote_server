import sys
import json
import os
import logging
import argparse
from service import Service
from queue import Queue, Empty
from threading import Thread
import time
from flask import Flask, request

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_path = os.path.abspath(os.path.dirname(__file__))
root_path = os.path.abspath(os.path.join(file_path, '../'))
print(root_path)
sys.path.insert(0, root_path)

SERVICE_REGISTER = {}

qps = 256
latency = 1 / qps


server = Flask(__name__)


@server.route("/")
def hello_world():
    return "<p>Hello, Win Server!</p>"



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str, required=True, help="端口号, 服务启动的端口号")
    args = parser.parse_args()
    port = args.port

    for name in SERVICE_REGISTER:
        SERVICE_REGISTER[name].listen()

    message = "\n".join(["service"] + [f"{k}:{v.to_dict()}" for k, v in SERVICE_REGISTER.items()])
    logger.info(message)

    server.run(host="0.0.0.0", port=f"{port}", processes=True)
    logger.info(f"start serving")

    for name in SERVICE_REGISTER:
        SERVICE_REGISTER[name].stop()


if __name__ == '__main__':
    main()