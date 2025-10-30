
import multiprocessing
import sys
import json
import os
import logging
import uuid
import logging.config


logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_path = os.path.abspath(os.path.dirname(__file__))
root_path = os.path.abspath(os.path.join(file_path, '../'))
print(root_path)
sys.path.insert(0, root_path)


class Task(object):

    def __init__(self, request_data):
        self.task_id = self.generate_task_id()
        self.request_data = request_data
        self.task_type = self.request_data.get("task_type", "")
        self.model_name = self.request_data.get("model_name", "")
        self.message = self.request_data.get("message", "")
        self.text = self.request_data.get("text", "")
        self.context = self.request_data.get("context", "")
        self.keyword = self.request_data.get("keyword", "")
        self.cde_params = self.request_data.get("cde_params", {})
        self.dwg_params = self.request_data.get("dwg_params", {})
        self.task_status = "waiting"
        self.task_results = None

    def __repr__(self):
        return f"{self.task_id}:{self.task_type}:{self.model_name}"

    @staticmethod
    def generate_task_id():
        return uuid.uuid1().hex

    def set_result(self, res):
        self.task_results = res

    def set_finish(self):
        self.task_status = "finished"

    def set_running(self):
        self.task_status = "running"

    def set_failed(self):
        self.task_status = "failed"

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "model_name": self.model_name,
            "message": self.message,
            "text": self.text,
            "context": self.context,
            "keyword": self.keyword,
            "task_status": self.task_status,
            "task_results": self.task_results,
            "cde_params": self.cde_params,
            "dwg_params": self.dwg_params,
        }

    def run(self):
        pass