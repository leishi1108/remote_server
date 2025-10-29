import sys
import os
import json
import logging
import argparse
from flask import Flask, request
from task import Task
from queue import Queue, Empty
from threading import Thread
import time
# from utils.metrics_utils import MetricsHelper, mcli

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Service(object):
    def __init__(self, name, interface, handler, server=None, qps=256, max_batch_size=128, consume_type="single", consume_worker=1):
        self.name = name
        self.interface = interface
        self.handler = handler
        self.qps = qps
        self.latency = 1 / qps
        self.max_batch_size = max_batch_size
        self.consume_worker = consume_worker
        self.queue = Queue(10 * self.qps)
        self.interface_func = self._build_interface_func()

        if consume_type == "single":
            self.consume_func = self._consume
        elif consume_type == "batch":
            self.consume_func = self._batch_consume
        else:
            raise ValueError(f"not support consume_type {consume_type}")
        self.consume_process = [Thread(target=self.consume_func, args=(i,)) for i in range(self.consume_worker)]

        if server is not None:
            server.add_url_rule(f'{interface}', view_func=self.interface_func)

    def _build_interface_func(self):
        def interface_func():
            time0 = time.time() * 1000
            logger.info(f"{self.name}: func call {time0}")

            tags = {
                'traffic': "upstream",
                'interface': self.interface,
            }

            # with MetricsHelper(name=self.name, tags=tags):
            req_data = json.loads(request.data.decode("utf-8"))
            task = Task(request_data=req_data)
            self.queue.put(task)
            logger.info(f"{self.name}: put task")
            while True:
                time.sleep(self.latency)
                if task.task_status in ["finished", "failed"]:
                    break

            time1 = time.time() * 1000
            logger.info(f"{self.name} task: {task.to_dict()} {time1}.")
            logger.info(f"{self.name} task: time diff {time1 - time0} ms.")
            return json.dumps(task.to_dict(), ensure_ascii=False)

        interface_func.__name__ = f"{self.name}_{self.handler.__class__.__name__}"

        return interface_func

    def to_dict(self):
        return {
            "name": self.name,
            "interface": self.interface,
            "handler": f"{self.handler.__class__.__name__}",
            "interface_func": f"{self.interface_func.__name__}",
        }

    def listen(self):
        for p in self.consume_process:
            p.start()

    def stop(self):
        for inx, p in enumerate(self.consume_process):
            logger.info(f"begin to join {self.name}_{self.handler.__class__.__name__} {inx}/{self.consume_worker}")
            p.join()
            logger.info(f"finish join {self.name}_{self.handler.__class__.__name__} {inx}/{self.consume_worker}")

    def _consume(self, worker_id):
        try:
            task = self.queue.get(block=True, timeout=self.latency)
        except Empty:
            task = None
            pass
        time0 = time.time() * 1000
        while True:
            time1 = time.time() * 1000
            time_diff = time1 - time0
            # print(f"worker {worker_id} time_diff {time_diff} ms")
            try:
                # print(f"worker {worker_id} consume_data instance {task}")
                if task is not None:
                    result = self.handler(task.to_dict())
                    task.set_result(result)
                    task.set_finish()
                # print(f"worker {worker_id} consume_data instance {task} end")
            except Exception as e:
                print(f"consume failed, instance={task.to_dict()}, exception={e}, process will stop early")
                task.set_failed()

            try:
                task = self.queue.get(block=True, timeout=self.latency)
            except Empty:
                task = None
                pass

    def _batch_consume(self, worker_id):
        batch_instances = []
        batch_tasks = []
        try:
            task = self.queue.get(block=True, timeout=self.latency)
        except Empty:
            task = None
            pass
        time0 = time.time() * 1000
        while True:
            time1 = time.time() * 1000
            time_diff = time1 - time0
            # print(f"worker {worker_id} time_diff {time_diff} ms")
            # print(f"worker {worker_id} consume_data instance {task}")
            if len(batch_instances) >= self.max_batch_size or time_diff >= self.max_batch_size:
                # print(f"worker {worker_id} predict begin")
                try:
                    results = self.handler(batch_instances)
                    # print(f"local_llm_consume results {results}")
                    # print(f"worker {worker_id} predict end")
                    assert len(results) == len(batch_instances), f'result:{len(results)} data:{len(batch_instances)}'
                    for i, result in enumerate(results):
                        batch_tasks[i].set_result(result)
                        batch_tasks[i].set_finish()
                except Exception as e:
                    print(
                        f"batch_consume consume failed, instance={task.to_dict()}, exception={e}, process will stop early")
                    for i, result in enumerate(batch_instances):
                        batch_tasks[i].set_failed()

                batch_instances = []
                batch_tasks = []
                time0 = time.time() * 1000
            if task is not None:
                batch_instances.append(task.to_dict())
                batch_tasks.append(task)
                # print(f"worker {worker_id} consume_data instance {task} end")

            try:
                task = self.queue.get(block=True, timeout=self.latency)
            except Empty:
                task = None
                pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=str, required=True, help="端口号, 服务启动的端口号")
    args = parser.parse_args()
    port = args.port

    # server = Flask(__name__)
    #
    # from cde_service_handler.cde_partial_client import CdePartialClient
    # client = CdePartialClient(cde_params_key="cde_params", task_type_key="task_type", url="http://10.127.91.1:3065")
    #
    # s1 = Service("测试1", "/cde1", client.run, server)
    # s1.listen()
    # s2 = Service("测试2", "/cde2", client.run, server)
    # s2.listen()
    #
    # server.run(host="0.0.0.0", port=f"{port}", processes=True)
    #
    # s1.stop()
    # s2.stop()
