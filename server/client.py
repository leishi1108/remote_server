import logging
import json
import requests
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

UTC_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class RemoteServerClient(object):
    def __init__(self, url=None):
        if url is not None:
            self.url = url
        else:
            self.url = "http://10.127.91.94:9001"

        rsp = requests.get(url=f"{self.url}/", timeout=60)
        print(rsp._content.decode("utf-8"))

    def list_file(self, instance):
        data = json.dumps(instance, ensure_ascii=False)

        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.get(url=f"{self.url}/files", data=data.encode("utf-8"), timeout=60)
                result = json.loads(rsp._content)["data"]
                return result
            except Exception as e:
                trial += 1
                logger.info(f"failed to get {self.url}/files")
                time.sleep(0.1)
                return None

    def delete_file(self, instance):
        file = instance["file"] if "file" in instance else None

        if file is None:
            logger.info(f"delete failed, file {file} is None")
            time.sleep(0.1)
            return None

        request = {"folder": instance["folder"] if "folder" in instance else None}
        data = json.dumps(request, ensure_ascii=False)

        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.delete(url=f"{self.url}/files/{file}", data=data.encode("utf-8"), timeout=60)
                result = json.loads(rsp._content)
                return result
            except Exception as e:
                trial += 1
                logger.info(f"failed to delete {self.url}/files/{file}")
                time.sleep(0.1)
                return None

    def upload_file(self, instance):
        local_file_path = instance["local_file_path"] if "local_file_path" in instance else None
        if local_file_path is None:
            logger.info(f"upload_file failed, local_file_path {local_file_path} is None")
            return None

        local_file = open(local_file_path, "rb")
        files = {'file': (local_file_path.split('/')[-1], local_file)}

        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.post(url=f"{self.url}/upload", files=files, timeout=60)
                result = json.loads(rsp._content)
                return result
            except Exception as e:
                trial += 1
                logger.info(f"failed to upload_file local_file_path {local_file_path}")
                time.sleep(0.1)
                return None

    def download_file(self, instance):

        file = instance["file"] if "file" in instance else None

        if file is None:
            logger.info(f"download failed, file {file} is None")
            time.sleep(0.1)
            return None

        request = {"folder": instance["folder"] if "folder" in instance else None}
        data = json.dumps(request, ensure_ascii=False)

        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.get(url=f"{self.url}/download/{file}", data=data.encode("utf-8"), timeout=60)
                return rsp
            except Exception as e:
                trial += 1
                logger.info(f"failed to download {self.url}/download/{file}")
                time.sleep(0.1)
                return None

    def dwg_decode(self, instance):
        dwg_file_path = instance["dwg_file_path"] if "dwg_file_path" in instance else None
        svg_file_folder = instance["svg_file_folder"] if "svg_file_folder" in instance else None

        if dwg_file_path is None:
            logger.info(f"dwg_decode failed, dwg_file_path {dwg_file_path} is None")
            return None

        if svg_file_folder is None:
            logger.info(f"dwg_decode failed, svg_file_folder {svg_file_folder} is None")
            return None

        request = {
            "dwg_params": {
                "dwg_file_path": dwg_file_path,
                "svg_file_folder": svg_file_folder,
            }
        }
        data = json.dumps(request, ensure_ascii=False)

        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.get(url=f"{self.url}/dwg_decode", data=data.encode("utf-8"), timeout=60)
                result = json.loads(rsp._content)
                return result
            except Exception as e:
                trial += 1
                logger.info(f"failed to dwg_decode {self.url}/dwg_decode/{dwg_file_path}")
                time.sleep(0.1)
                return None

    def _interface_call(self, instance, interface):
        data = json.dumps(instance, ensure_ascii=False)

        trial = 0
        retry = 3
        while trial < retry:
            try:
                rsp = requests.get(url=f"{self.url}/{interface}", data=data.encode("utf-8"), timeout=60)
                result = json.loads(rsp._content)["task_results"]
                return result
            except Exception as e:
                trial += 1
                logger.info(f"failed to get {self.url}/{interface}")
                time.sleep(0.1)
                # raise Exception(f"failed to get {self.url}/{interface}")
                return None


if __name__ == '__main__':
    remote_server_client = RemoteServerClient()

    list_test_instance = {"folder": "E:\\dwgData"}
    list_result = remote_server_client.list_file(list_test_instance)
    print(f"list_result {list_result}")

    upload_test_instance = {"local_file_path": "/Users/shilei.1108/corpus/清单编制/重庆中海房建项目图纸-建筑和结构/19.10.26 中海项目结构最终版图纸（8.31）/中海项目结构最终版图纸（8.31）/7号楼OK/7号楼结构图纸/7#楼大样_t7_t7.dwg"}
    upload_result = remote_server_client.upload_file(upload_test_instance)
    print(f"upload_result {upload_result}")

    dwg_decode_test_instance = {
        "dwg_file_path": "E:\\dwgData\\7c09b8dacee64f9c806d534a356b638b.dwg",
        "svg_file_folder": "E:\\svgData\\7c09b8dacee64f9c806d534a356b638b"}

    dwg_decode_result = remote_server_client.dwg_decode(dwg_decode_test_instance)
    print(f"dwg_decode_result {dwg_decode_result}")

    download_test_instance = {"folder": "E:\\svgData", "file": "7c09b8dacee64f9c806d534a356b638b"}
    download_result = remote_server_client.download_file(download_test_instance)
    print(f"download_result {download_result}")
    save_path = "/Users/shilei.1108/corpus/清单编制/矢量图/7#楼大样_t7_t7.zip"
    if download_result.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in download_result.iter_content(chunk_size=8192):
                f.write(chunk)

    delete_test_instance = {"folder": "E:\\svgData", "file": "7c09b8dacee64f9c806d534a356b638b"}
    delete_result = remote_server_client.delete_file(delete_test_instance)
    print(f"delete_result {delete_result}")
