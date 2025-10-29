import requests
import time
import json
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class ModelServerClient(object):

    def __init__(self, url=None):
        if url is not None:
            self.url = url
        else:
            self.url = "http://10.0.79.103:9001/"
        rsp = requests.get(url=f"{self.url}/", timeout=60)
        print(rsp._content.decode("utf-8"))

    def chat(self, instance):
        data = json.dumps(instance, ensure_ascii=False)

        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.get(url=f"{self.url}/chat", data=data.encode("utf-8"), timeout=60)
                result = json.loads(rsp._content)["task_results"]
                return result
            except Exception as e:
                trial += 1
                logger.info(f"failed to get chat {trial}/{retry} {self.url} {rsp._content} {rsp}")
                time.sleep(0.1)
                raise Exception("failed to get chat")

    def predict_item_classify(self, instance):

        data = json.dumps(instance, ensure_ascii=False)

        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.get(url=f"{self.url}/predict_item_classify", data=data.encode("utf-8"), timeout=60)
                result = json.loads(rsp._content)["task_results"]
                return result
            except Exception as e:
                trial += 1
                logger.info(f"failed to predict_item_classify {trial}/{retry} {self.url} {rsp._content} {rsp}")
                time.sleep(0.1)

    def llm_partial(self, instance):

        data = json.dumps(instance, ensure_ascii=False)

        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.get(url=f"{self.url}/llm_partial", data=data.encode("utf-8"), timeout=60)
                result = json.loads(rsp._content)["task_results"]
                return result
            except Exception as e:
                trial += 1
                logger.info(f"failed to predict_partial {trial}/{retry} {self.url} {rsp._content} {rsp}")
                time.sleep(0.1)

    def glodon_llm_partial(self, instance):

        data = json.dumps(instance, ensure_ascii=False)

        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.get(url=f"{self.url}/glodon_llm_partial", data=data.encode("utf-8"), timeout=60)
                result = json.loads(rsp._content)["task_results"]
                return result
            except Exception as e:
                trial += 1
                logger.info(f"failed to glodon_predict_partial {trial}/{retry} {self.url} {rsp._content} {rsp}")
                time.sleep(0.1)

    def cde_partial(self, instance):

        data = json.dumps(instance, ensure_ascii=False)
        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.get(url=f"{self.url}/cde_partial", data=data.encode("utf-8"), timeout=60)
                result = json.loads(rsp._content)["task_results"]
                return result
            except Exception as e:
                trial += 1
                logger.info(f"failed to glodon_predict_partial {trial}/{retry} {self.url} {rsp._content} {rsp}")
                time.sleep(0.1)


if __name__ == '__main__':
    model_server_client = ModelServerClient(url="http://10.0.79.103:9001/")
    test_instance = {"text": "地库-建筑|后浇带",
                     "context": "筏板后浇带 1.混凝土种类:预拌泵送商品混凝土 2.混凝土强度等级:C40 3、抗渗等级：P6 4、掺膨胀剂 5、钢板止水带与拉网一层"}

    time0 = time.time() * 1000
    result = model_server_client.llm_partial(test_instance)
    time1 = time.time() * 1000
    time_diff = time1 - time0
    category = result["category"]
    print(f"category {category} time_diff {time_diff} ms")

    time0 = time.time() * 1000
    result = model_server_client.glodon_llm_partial(test_instance)
    time1 = time.time() * 1000
    time_diff = time1 - time0
    category = result["category"]
    print(f"category {category} time_diff {time_diff} ms")

    test_instance = {
        "cde_params": {
            "requestID": "10086",
            "contents": [
                {
                    "uid": "7",
                    "projectName": "A区地下室土建工程",
                    "upperItemName": "土建专业/钢筋混凝土工程",
                    "itemName": "直形墙",
                    "itemProperty": "项目特征：\t1、混凝土种类:商品砼    2、施工区域：大地下室"
                }
            ]
        },
        "task_type": "清单"}

    time0 = time.time() * 1000
    result = model_server_client.cde_partial(test_instance)
    time1 = time.time() * 1000
    time_diff = time1 - time0
    print(f"result {result} time_diff {time_diff} ms")


