from flask import Flask, render_template, request, redirect, url_for, Response
import os
from werkzeug.utils import secure_filename
import cv2
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
import base64
from typing import Optional
from qrcode.image.pil import PilImage

from PIL import Image
import numpy
import io

app = Flask(__name__,
    template_folder="../templates",
    static_folder="../static"
)

app.config['UPLOAD_FOLDER'] = 'static/uploads'  
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  

def generate_qr_code(data: str,
                     version: int = 5,
                     box_size: int = 10,
                     border: int = 4) -> PilImage:
    """
    生成二维码图片
    :param data: 要编码的字符串
    :param version: 二维码复杂度 (1-40)
    :param box_size: 每个小格子的像素数
    :param border: 边框宽度（单位：格子数）
    :return: PIL Image 对象
    """
    qr = qrcode.QRCode(
        version=version,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")

def adjust_create_time(original_str: str) -> str:
    """
    将 URL 参数中的 createTime 增加 1 小时
    :param original_str: 原始带参数字符串
    :return: 调整后的字符串
    """
    try:
        parts = original_str.split('&')

        for i in range(len(parts)):
            if parts[i].startswith('createTime='):
                
                _, time_value = parts[i].split('=', 1)

                dt = datetime.strptime(time_value, "%Y-%m-%dT%H:%M:%S.%f")

                dt += timedelta(hours=1)

                new_time = dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]  

                parts[i] = f"createTime={new_time}"
                break

        return '&'.join(parts)

    except Exception as e:
        print(f"处理失败: {str(e)}")
        return original_str  

def allowed_file(filename: str) -> bool:
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def read_qr_code(file_bytes: bytes) -> Optional[str]:
    """
    解析上传文件中的二维码
    :param file_bytes: 上传文件的二进制数据
    :return: 解码后的字符串，失败返回 None
    """
    try:
        if len(file_bytes) > app.config['MAX_CONTENT_LENGTH']:
            raise ValueError("文件过大")
        image = Image.open(io.BytesIO(file_bytes))
        img = cv2.cvtColor(numpy.asarray(image), cv2.COLOR_RGB2BGR)
        detector = cv2.wechat_qrcode_WeChatQRCode()
        data, _, _ = detector.detectAndDecode(img)
        return data or None
    except Exception as e:
        print(f"二维码解析失败: {str(e)}")
        return None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file selected"

        file = request.files['file']

        if file.filename == '':
            return "No file selected"
        if not allowed_file(file.filename):
            return "Invalid file type"

        if file:
            file_data = file.read()
            qr_text = read_qr_code(file_data)
            if qr_text:
                return redirect(url_for('show_image', filename='pic', qr_text=qr_text))
            else:
                return "未检测到二维码或读取失败"

    return render_template('index.html')


@app.route('/show/<filename>')
def show_image(filename):
    qr_text = request.args.get('qr_text', '')
    qr_data = request.args.get('data', adjust_create_time(qr_text))

    try:
        img = generate_qr_code(qr_data)  
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0) 
        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return render_template('show.html',
                               qr_text=qr_text,
                               adjusted_text=qr_data,
                               image_data=image_data,
                               filename=filename)

    except Exception as e:
        return f"二维码生成失败: {str(e)}", 500

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)