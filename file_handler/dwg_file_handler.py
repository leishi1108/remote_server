import logging
import json
import requests
import time
import tqdm
from multiprocessing.pool import ThreadPool
import copy
import datetime
import os
from collections import defaultdict
from concurrent import futures
import urllib3
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

UTC_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class SimpleDwgClient(object):

    def __init__(self):
        pass

    def _performance(self):
        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.post(url=f"{self.url}/scheme/performance", data=None, timeout=60)
                data = json.loads(rsp._content.decode("utf-8"))
                return data
            except Exception as e:
                trial += 1
                logger.info(f"failed to get cde list process {trial}/{retry} {self.url} {rsp.content} {rsp}")
                time.sleep(0.1)
                raise Exception("faied to get cde performance process")

    def _list_debug_process(self, request):
        request_data = json.dumps(request, ensure_ascii=False)
        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.post(url=f"{self.url}/scheme/bom_debug", data=request_data.encode("utf-8"), timeout=60)
                data = json.loads(rsp._content.decode("utf-8"))
                return data
            except Exception as e:
                trial += 1
                logger.info(f"failed to get cde list process {trial}/{retry} {self.url} {rsp.content} {rsp}")
                time.sleep(0.1)
                raise Exception("faied to get cde list debug process")

