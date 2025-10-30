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
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

UTC_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class SimpleDwgClient(object):

    def __init__(self):
        self.cmd = "E:\dwg\ReleaseDebug\CheckCADTool.exe"

    def _prepare_data(self, instance):

        assert "dwg_file_path" in instance, f"dwg_file_path not in  request {instance}"
        assert "svd_file_folder" in instance, f"svd_file_folder not in  request {instance}"

        dwg_request = {
            "dwg_file_path": instance["dwg_file_path"],
            "svd_file_folder": instance["svd_file_folder"],
            "is_colorful": 1,
            "is_svd": 1,
        }

        return dwg_request

    def run(self, instance):
        """使用 subprocess.run 执行 exe 文件"""

        dwg_request = self._prepare_data(instance)
        try:
            os.makedirs(dwg_request["svd_file_folder"], exist_ok=True)

            result = subprocess.run([self.cmd, "-p", f"{dwg_request['dwg_file_path']}", "-o", f"{dwg_request['svd_file_folder']}", "-t", dwg_request['is_svd'], "-c", dwg_request['is_colorful']],
                                    timeout=10, capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            print("命令执行超时")

        return os.listdir(dwg_request['svd_file_folder'])


if __name__ == '__main__':
    test_instance = {
        "dwg_file_path": "E:\\dwgData\\42a4159835344d4c8d8f7c7cd640b8d3.dwg",
        "svd_file_folder": "E:\\svgData\\42a4159835344d4c8d8f7c7cd640b8d3",
        "is_colorful": 1,
        "is_svd": 1,
    }

    simple_dwg_client = SimpleDwgClient()
    output = simple_dwg_client.run(test_instance)
    print(f"simple_dwg_client output {output}")

