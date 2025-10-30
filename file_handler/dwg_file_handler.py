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

    def __init__(self, dwg_params_key="dwg_params"):
        self.cmd = "E:\dwg\ReleaseDebug\CheckCADTool.exe"
        self.dwg_params_key = dwg_params_key

    def _prepare_data(self, instance):

        assert self.dwg_params_key in instance, f"dwg params key {self.dwg_params_key} not in instance {instance}"
        dwg_request = instance[self.dwg_params_key]

        assert "dwg_file_path" in dwg_request, f"dwg_file_path not in  dwg_request {dwg_request}"
        assert "svg_file_folder" in dwg_request, f"svg_file_folder not in  dwg_request {dwg_request}"

        dwg_request["is_colorful"] = "1"
        dwg_request["is_svg"] = "1"

        return dwg_request

    def run(self, instance):
        """使用 subprocess.run 执行 exe 文件"""

        dwg_request = self._prepare_data(instance)
        try:
            os.makedirs(dwg_request["svg_file_folder"], exist_ok=True)

            result = subprocess.run([self.cmd, "-p", f"{dwg_request['dwg_file_path']}", "-o", f"{dwg_request['svg_file_folder']}", "-t", f"{dwg_request['is_svg']}", "-c", f"{dwg_request['is_colorful']}"])
                                    # timeout=10, capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            result = None
            print("命令执行超时")

        return {"returncode": result.returncode}


if __name__ == '__main__':
    test_instance = {
        "dwg_params": {
            "dwg_file_path": "E:\\dwgData\\42a4159835344d4c8d8f7c7cd640b8d3.dwg",
            "svg_file_folder": "E:\\svgData\\42a4159835344d4c8d8f7c7cd640b8d3",
            "is_colorful": 1,
            "is_svg": 1,
        }
    }

    simple_dwg_client = SimpleDwgClient(dwg_params_key="dwg_params")
    output = simple_dwg_client.run(test_instance)
    print(f"simple_dwg_client output {output}")

