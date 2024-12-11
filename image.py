# image.py
from flask import Blueprint, request
import os
import constants
from decorators import login_required, response_format
from werkzeug.utils import secure_filename

image_bp = Blueprint('image', __name__)


# 设置允许上传的文件类型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 创建事件
@image_bp.route('/image/upload', methods=['POST'])
@login_required
@response_format
def upload():
    from app import BASE_DIR
    if 'file' not in request.files:
        return {"code": constants.RESULT_FAIL, "message": "没有文件上传"}

    file = request.files['file']

    if file.filename == '':
        return {"code": constants.RESULT_FAIL, "message": "没有选择文件"}

    # 检查文件大小
    if request.content_length > MAX_FILE_SIZE:
        return {"code": constants.RESULT_FAIL, "message": "文件大小不能超过 1MB"}

    if not allowed_file(file.filename):
        return {"code": constants.RESULT_FAIL, "message": "不允许的文件类型"}

    # 生成安全的文件名并保存文件
    filename = secure_filename(file.filename)
    upload_folder = os.path.join(BASE_DIR, 'static/image')  # 上传目录
    os.makedirs(upload_folder, exist_ok=True)  # 创建目录（如果不存在）
    file_path = os.path.join(upload_folder, filename)

    file.save(file_path)  # 保存文件

    # 生成可访问的 URL
    url = f"/static/image/{filename}"

    return {
        "code": constants.RESULT_SUCCESS,
        "url": url
    }
