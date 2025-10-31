import sys
import json
import os
import logging
import argparse
from service import Service
from queue import Queue, Empty
from threading import Thread
import time
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import zipfile
import uuid
from file_handler.dwg_file_handler import SimpleDwgClient
import shutil

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

UPLOAD_DIR = "E:\dwgData"
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip', 'rar', 'mp4', 'mp3', 'xls', 'xlsx', 'ppt', 'pptx', 'dwg',
}

DOWNLOAD_DIR = "E:\svgData"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

server.config['UPLOAD_FOLDER'] = UPLOAD_DIR
server.config['DOWNLOAD_FOLDER'] = DOWNLOAD_DIR
server.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

@server.route("/")
def hello_world():
    return "<p>Hello, Win Server!</p>"

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_info(folder, filename):
    """获取文件信息"""
    file_path = os.path.join(folder, filename)
    if os.path.exists(file_path):
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'upload_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    return None


@server.route('/upload', methods=['POST'])
def upload_file():
    """
    文件上传接口
    支持表单上传和二进制流上传
    """
    try:
        # 检查是否有文件部分
        if 'file' not in request.files and request.content_length > 0:
            # 尝试从二进制流读取
            return upload_from_stream(request)

        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有选择文件',
                'error_code': 'NO_FILE'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '文件名不能为空',
                'error_code': 'EMPTY_FILENAME'
            }), 400

        if file and allowed_file(file.filename):
            print(f"file: {file}\n")

            # 生成安全的文件名
            original_filename = secure_filename(file.filename)
            print(f"original_filename: {original_filename}\n")

            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''

            # 生成唯一文件名避免冲突
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else uuid.uuid4().hex
            save_filename = unique_filename
            print(f"save_filename: {save_filename}\n")

            # 保存文件
            file_path = os.path.join(server.config['UPLOAD_FOLDER'], save_filename)
            file.save(file_path)

            # 获取文件信息
            file_info = get_file_info(server.config['UPLOAD_FOLDER'], save_filename)

            return jsonify({
                'success': True,
                'message': '文件上传成功',
                'data': {
                    'original_filename': file.filename,
                    'saved_filename': save_filename,
                    'file_size': file_info['size'] if file_info else 0,
                    'upload_time': file_info['upload_time'] if file_info else datetime.now().isoformat(),
                    'download_url': file_path,
                    'file_id': save_filename.rsplit('.', 1)[0]  # 返回文件ID（不含扩展名）
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'文件类型不允许，允许的类型: {", ".join(ALLOWED_EXTENSIONS)}',
                'error_code': 'INVALID_FILE_TYPE'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}',
            'error_code': 'UPLOAD_ERROR'
        }), 500


def upload_from_stream(request):
    """从二进制流上传文件"""
    try:
        # 从请求头获取文件名
        filename = request.headers.get('X-File-Name')
        if not filename:
            return jsonify({
                'success': False,
                'message': '缺少文件名头信息',
                'error_code': 'MISSING_FILENAME_HEADER'
            }), 400

        filename = secure_filename(filename)

        if not allowed_file(filename):
            return jsonify({
                'success': False,
                'message': f'文件类型不允许，允许的类型: {", ".join(ALLOWED_EXTENSIONS)}',
                'error_code': 'INVALID_FILE_TYPE'
            }), 400

        # 生成唯一文件名
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else uuid.uuid4().hex

        # 保存文件
        file_path = os.path.join(server.config['UPLOAD_FOLDER'], unique_filename)
        with open(file_path, 'wb') as f:
            f.write(request.data)

        file_info = get_file_info(server.config['UPLOAD_FOLDER'], unique_filename)

        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'data': {
                'original_filename': filename,
                'saved_filename': unique_filename,
                'file_size': file_info['size'] if file_info else len(request.data),
                'upload_time': file_info['upload_time'] if file_info else datetime.now().isoformat(),
                'download_url': file_path,
                'file_id': unique_filename.rsplit('.', 1)[0]
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'流式上传失败: {str(e)}',
            'error_code': 'STREAM_UPLOAD_ERROR'
        }), 500


@server.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """文件下载接口"""
    try:
        req_data = json.loads(request.data.decode("utf-8"))

        folder = req_data["folder"] if "folder" in req_data and req_data["folder"] is not None else server.config['DOWNLOAD_FOLDER']
        print(f"folder {folder}\n")
        filename = secure_filename(filename)
        print(f"filename {filename}\n")
        file_path = os.path.join(folder, filename)
        print(f"file_path {file_path}\n")

        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': '文件不存在',
                'error_code': 'FILE_NOT_FOUND'
            }), 404

        if os.path.isdir(file_path):
            output_zip_path = os.path.join(folder, f"{filename}.zip")
            with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:

                # 遍历文件夹中的所有文件和子文件夹
                for root, dirs, files in os.walk(file_path):
                    for sub_file in files:
                        sub_file_path = os.path.join(root, sub_file)
                        # 计算在 ZIP 文件中的相对路径
                        arcname = os.path.relpath(sub_file_path, file_path)

                        # 添加到 ZIP 文件
                        zipf.write(sub_file_path, arcname)
                        print(f"添加文件: {arcname}")

            print(f"压缩完成! 文件大小: {os.path.getsize(output_zip_path)} 字节")
            file_path = output_zip_path

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'下载失败: {str(e)}',
            'error_code': 'DOWNLOAD_ERROR'
        }), 500


@server.route('/files', methods=['GET'])
def list_files():
    """获取文件列表"""
    try:
        req_data = json.loads(request.data.decode("utf-8"))
        folder = req_data["folder"] if "folder" in req_data and req_data["folder"] is not None else server.config['UPLOAD_FOLDER']
        print(f"folder {folder}\n")

        files = []
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                file_info = get_file_info(folder, filename)
                files.append({
                    'filename': filename,
                    'size': file_info['size'] if file_info else 0,
                    'upload_time': file_info['upload_time'] if file_info else '',
                    'download_url': file_path,
                })

        return jsonify({
            'success': True,
            'data': {
                'files': files,
                'total_count': len(files)
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取文件列表失败: {str(e)}',
            'error_code': 'LIST_FILES_ERROR'
        }), 500


@server.route('/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """删除文件"""
    try:
        req_data = json.loads(request.data.decode("utf-8"))

        folder = req_data["folder"] if "folder" in req_data and req_data["folder"] is not None else server.config['UPLOAD_FOLDER']

        assert folder in [UPLOAD_DIR, DOWNLOAD_DIR], f"delete folder must in [{UPLOAD_DIR}, {DOWNLOAD_DIR}], but {folder} now"
        print(f"folder {folder}\n")
        filename = secure_filename(filename)
        print(f"filename {filename}\n")
        file_path = os.path.join(folder, filename)
        print(f"file_path {file_path}\n")

        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': '文件不存在',
                'error_code': 'FILE_NOT_FOUND'
            }), 404

        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)

        return jsonify({
            'success': True,
            'message': '文件删除成功'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除文件失败: {str(e)}',
            'error_code': 'DELETE_ERROR'
        }), 500


@server.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'File Upload Service'
    }), 200



dwg_client = SimpleDwgClient(dwg_params_key="dwg_params")

service_list = [
    {"name": "DWG解码", "interface": "/dwg_decode", "handler": dwg_client.run},
]

SERVICE_REGISTER = {s["name"]: Service(server=server, **s) for s in service_list}

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