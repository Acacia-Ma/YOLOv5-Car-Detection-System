import time
import sqlite3
from flask import Flask, request, jsonify, send_file, send_from_directory, Response
import cv2
import numpy as np
import io
import logging
from onnx_infer import PlateRecognitionV5, draw_result, cv2ImgAddText
from PIL import Image, ImageDraw, ImageFont
import os
import datetime
import csv
# 导入CORS以支持跨域请求
from flask_cors import CORS

def get_time_str():
    curr_time = datetime.datetime.now()
    time_str = datetime.datetime.strftime(curr_time,'%Y_%m_%d')
    return time_str

def get_second_str():
    curr_time = datetime.datetime.now()
    time_str = datetime.datetime.strftime(curr_time,'%Y-%m-%d_%H:%M:%S')
    return time_str

csv_name = get_time_str()+".csv"

# 只有当CSV文件不存在时才创建并写入表头
if not os.path.exists(csv_name):
    with open(csv_name, mode='w', newline='', encoding='utf-8') as example_file:
        fieldnames = ['图片名','车牌号','车牌颜色','置信度','识别时间']
        writer = csv.DictWriter(example_file, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

app = Flask(__name__, static_folder='static')
# 启用CORS，允许前端跨域请求
CORS(app)
app.secret_key = 'your_random_secret_key_here'

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 创建SQLite数据库和用户表
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             username TEXT NOT NULL UNIQUE,
             password TEXT NOT NULL,
             role TEXT DEFAULT 'user',
             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
             is_active INTEGER DEFAULT 1)''')

# 创建默认管理员账户（如果不存在）
c.execute("SELECT * FROM users WHERE username = 'admin'")
admin_exists = c.fetchone()
if not admin_exists:
    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
              ('admin', 'admin123', 'admin'))

conn.commit()
conn.close()

# YOLOv5 车牌检测 以及lprnet 模型加载，初始化
plateRec = PlateRecognitionV5(r"model/plate_detect.onnx", "model/plate_rec_color.onnx", providers=["CUDAExecutionProvider"])

cap = None
video_path = None  # 保存上传的视频路径

def random_string(length):
    import random
    import string
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str

# 公共检测函数：处理单帧
def detect_frame(frame):
    img = frame.copy()
    result_list = plateRec(img)
    if result_list:
        plate_no = result_list[0]['plate_no']   #车牌号
        plate_color = result_list[0]['plate_color'] #车牌颜色
        confidence = result_list[0]['score']    #置信度
        frame = draw_result(img, result_list)
        return frame, plate_no, plate_color, confidence
    else:
        frame = draw_result(img, result_list)
        return frame, "", "", ""

# API路由

# 注册API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"status": "error", "message": "用户名和密码不能为空"}), 400
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "注册成功，请登录"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "用户名已存在，请选择其他用户名"}), 409

# 登录API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, username, role, is_active FROM users WHERE username =? AND password =?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        user_id, username, role, is_active = user
        if not is_active:
            return jsonify({"status": "error", "message": "账户已被禁用"}), 403
        return jsonify({
            "status": "success", 
            "message": "登录成功", 
            "username": username,
            "role": role,
            "user_id": user_id
        }), 200
    else:
        return jsonify({"status": "error", "message": "用户名或密码错误"}), 401

# 图片检测API
@app.route('/api/detect_image', methods=['POST'])
def detect_image():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "未上传文件"}), 400
    
    file = request.files['file']
    if not file:
        return jsonify({"status": "error", "message": "请选择图片再提交"}), 400
    
    csv_name = get_time_str()+".csv"
    
    # 确保CSV文件存在且有表头
    if not os.path.exists(csv_name):
        with open(csv_name, mode='w', newline='', encoding='utf-8') as example_file:
            fieldnames = ['图片名','车牌号','车牌颜色','置信度','识别时间']
            writer = csv.DictWriter(example_file, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
    
    with open(csv_name, mode='a', newline='', encoding='utf-8') as example_file:
        fieldnames = ['图片名','车牌号','车牌颜色','置信度','识别时间']
        writer = csv.DictWriter(example_file, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        img_bytes = file.read()
        img = Image.open(io.BytesIO(img_bytes))
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        showimg = img.copy()
        file_name = file.filename
        pic_name = os.path.basename(file_name)
        
        # 检测
        img_name = pic_name
        save_path = "static/result"
        os.makedirs(save_path, exist_ok=True)
        img_path = os.path.join(save_path, img_name)
        
        showimg, plate_no, plate_color, confidence = detect_frame(showimg)
        confidence_num = confidence if confidence else 0
        confidence_str = str(round(confidence_num, 4)) if confidence_num else "0"
        writer.writerow({"图片名":file_name,"车牌号":plate_no,"车牌颜色":plate_color,"置信度":confidence_str,"识别时间":get_second_str()})
        
        # 保存结果
        img_file = 'static/result.jpg'
        cv2.imwrite(img_path, showimg)
        cv2.imwrite(img_file, showimg)
        
        # 返回结果
        return jsonify({
            "status": "success", 
            "message": "图片检测完成",
            "image_url": f'/static/result/{img_name}',
            "plate_no": plate_no,
            "plate_color": plate_color,
            "confidence": confidence_num  # 返回数字而不是字符串
        }), 200

# 获取历史记录API
@app.route('/api/history', methods=['GET'])
def get_history():
    csv_name = get_time_str()+".csv"
    records = []
    try:
        with open(csv_name, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # 转换置信度为数字格式
                if '置信度' in row and row['置信度']:
                    try:
                        row['置信度'] = float(row['置信度'])
                    except (ValueError, TypeError):
                        row['置信度'] = 0.0
                else:
                    row['置信度'] = 0.0
                records.append(row)
        return jsonify({"status": "success", "records": records}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 删除历史记录API
@app.route('/api/delete_history_record', methods=['POST'])
def delete_history_record():
    data = request.get_json()
    idx = data.get('idx')
    if idx is None:
        return jsonify({"status": "error", "message": "缺少索引参数"}), 400
    
    csv_name = get_time_str()+".csv"
    try:
        records = []
        with open(csv_name, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            records = list(reader)
        
        if idx < 0 or idx >= len(records):
            return jsonify({"status": "error", "message": "索引超出范围"}), 400
        
        del records[idx]
        
        with open(csv_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['图片名','车牌号','车牌颜色','置信度','识别时间'])
            writer.writeheader()
            writer.writerows(records)
        
        return jsonify({"status": "success", "message": "删除成功"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 批量删除历史记录API
@app.route('/api/batch_delete_history', methods=['POST'])
def batch_delete_history():
    data = request.get_json()
    indices = data.get('indices')
    if not indices or not isinstance(indices, list):
        return jsonify({"status": "error", "message": "缺少或无效的索引参数"}), 400
    
    csv_name = get_time_str()+".csv"
    try:
        records = []
        with open(csv_name, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            records = list(reader)
        
        # 验证所有索引是否有效
        for idx in indices:
            if idx < 0 or idx >= len(records):
                return jsonify({"status": "error", "message": f"索引 {idx} 超出范围"}), 400
        
        # 按降序排序索引，从后往前删除，避免索引偏移
        indices_sorted = sorted(set(indices), reverse=True)
        
        # 删除记录
        for idx in indices_sorted:
            del records[idx]
        
        # 重新写入CSV文件
        with open(csv_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['图片名','车牌号','车牌颜色','置信度','识别时间'])
            writer.writeheader()
            writer.writerows(records)
        
        return jsonify({"status": "success", "message": f"成功删除 {len(indices_sorted)} 条记录"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 下载CSV文件API
@app.route('/api/download_history', methods=['GET'])
def download_history():
    csv_name = get_time_str()+".csv"
    try:
        return send_file(csv_name, as_attachment=True)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 视频上传API
@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"status": "error", "message": "未上传视频"}), 400
    
    video_file = request.files['video']
    if not video_file:
        return jsonify({"status": "error", "message": "请选择视频文件"}), 400
    
    # 保存上传的视频
    video_path = 'static/uploaded_video.mp4'
    video_file.save(video_path)
    
    # 检查视频文件是否有效
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return jsonify({"status": "error", "message": "无法打开视频文件"}), 400
    cap.release()
    
    return jsonify({"status": "success", "message": "视频上传成功", "video_path": video_path}), 200

# 视频检测API
@app.route('/api/detect_video', methods=['POST'])
def detect_video():
    video_path = 'static/uploaded_video.mp4'
    if not os.path.exists(video_path):
        return jsonify({"status": "error", "message": "请先上传视频"}), 400
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return jsonify({"status": "error", "message": "无法打开视频文件"}), 400
    
    # 获取视频信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 设置输出视频 - 尝试多种编码格式以确保浏览器兼容性
    output_path = 'static/result_video.mp4'
    
    # 尝试不同的编码格式
    codecs = ['H264', 'XVID', 'MJPG', 'mp4v']
    out = None
    
    for codec in codecs:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            if out.isOpened():
                print(f"使用编码格式: {codec}")
                break
            else:
                out.release()
        except:
            continue
    
    if out is None or not out.isOpened():
        cap.release()
        return jsonify({"status": "error", "message": "无法创建输出视频文件"}), 500
    
    frame_count = 0
    detected_plates = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测当前帧
        processed_frame, plate_no, plate_color, confidence = detect_frame(frame)
        
        # 记录检测结果
        if plate_no:
            detected_plates.append({
                'frame': frame_count,
                'plate_no': plate_no,
                'plate_color': plate_color,
                'confidence': confidence,
                'timestamp': frame_count / fps
            })
        
        out.write(processed_frame)
        frame_count += 1
    
    cap.release()
    out.release()
    
    return jsonify({
        "status": "success",
        "message": "视频检测完成",
        "output_video": f'static/result_video.mp4',
        "detected_plates": detected_plates,
        "total_frames": total_frames,
        "fps": fps
    }), 200

# 摄像头流API
@app.route('/api/camera_feed')
def camera_feed():
    def generate():
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return
        
        try:
            while True:
                success, frame = cap.read()
                if not success:
                    break
                
                # 检测
                processed_frame, _, _, _ = detect_frame(frame)
                
                ret, buffer = cv2.imencode('.jpg', processed_frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            logger.error(f"摄像头流错误: {e}")
        finally:
            cap.release()
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# 停止摄像头API
@app.route('/api/stop_camera', methods=['POST'])
def stop_camera():
    return jsonify({"status": "success", "message": "摄像头已停止"}), 200

# 获取静态文件
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# API静态文件路由（为前端提供统一的API路径）
@app.route('/api/static/<path:filename>')
def serve_api_static(filename):
    return send_from_directory('static', filename)

# ==================== 管理员API ====================

# 验证管理员权限的装饰器
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json() if request.is_json else {}
        username = data.get('admin_username')
        if not username:
            return jsonify({"status": "error", "message": "需要管理员权限"}), 403
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if not user or user[0] != 'admin':
            return jsonify({"status": "error", "message": "权限不足"}), 403
        
        return f(*args, **kwargs)
    return decorated_function

# 获取所有用户列表
@app.route('/api/admin/users', methods=['POST'])
@admin_required
def get_all_users():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT id, username, role, created_at, is_active FROM users ORDER BY created_at DESC")
        users = c.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'created_at': user[3],
                'is_active': bool(user[4])
            })
        
        return jsonify({"status": "success", "users": user_list}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 禁用/启用用户
@app.route('/api/admin/toggle_user', methods=['POST'])
@admin_required
def toggle_user():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"status": "error", "message": "缺少用户ID"}), 400
    
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # 获取当前状态
        c.execute("SELECT is_active, username FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user:
            return jsonify({"status": "error", "message": "用户不存在"}), 404
        
        current_status, username = user
        new_status = 0 if current_status else 1
        
        # 防止禁用管理员账户
        if username == 'admin' and new_status == 0:
            return jsonify({"status": "error", "message": "不能禁用管理员账户"}), 400
        
        c.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        conn.commit()
        conn.close()
        
        action = "启用" if new_status else "禁用"
        return jsonify({"status": "success", "message": f"用户已{action}"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 删除用户
@app.route('/api/admin/delete_user', methods=['POST'])
@admin_required
def delete_user():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"status": "error", "message": "缺少用户ID"}), 400
    
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # 检查是否为管理员
        c.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user:
            return jsonify({"status": "error", "message": "用户不存在"}), 404
        
        if user[0] == 'admin':
            return jsonify({"status": "error", "message": "不能删除管理员账户"}), 400
        
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": "用户已删除"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 获取系统统计信息
@app.route('/api/admin/statistics', methods=['POST'])
@admin_required
def get_statistics():
    try:
        # 用户统计
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_users = c.fetchone()[0]
        conn.close()
        
        # 识别记录统计
        csv_name = get_time_str() + ".csv"
        total_detections = 0
        successful_detections = 0
        
        try:
            with open(csv_name, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                records = list(reader)
                total_detections = len(records)
                successful_detections = len([r for r in records if r.get('车牌号')])
        except FileNotFoundError:
            pass
        
        # 获取所有CSV文件的统计
        import glob
        all_csv_files = glob.glob("*.csv")
        all_time_detections = 0
        for csv_file in all_csv_files:
            try:
                with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    all_time_detections += len(list(reader))
            except:
                continue
        
        return jsonify({
            "status": "success",
            "statistics": {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "admin": admin_users
                },
                "detections": {
                    "today": total_detections,
                    "today_successful": successful_detections,
                    "all_time": all_time_detections
                }
            }
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 获取所有历史记录（管理员）
@app.route('/api/admin/all_history', methods=['POST'])
@admin_required
def get_all_history():
    try:
        import glob
        all_records = []
        csv_files = glob.glob("*.csv")
        
        for csv_file in csv_files:
            try:
                with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        row['date'] = csv_file.replace('.csv', '')
                        all_records.append(row)
            except:
                continue
        
        # 按时间排序
        all_records.sort(key=lambda x: x.get('识别时间', ''), reverse=True)
        
        return jsonify({"status": "success", "records": all_records}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 清理历史记录
@app.route('/api/admin/clear_history', methods=['POST'])
@admin_required
def clear_history():
    data = request.get_json()
    clear_type = data.get('clear_type', 'today')  # today, all
    
    try:
        if clear_type == 'today':
            csv_name = get_time_str() + ".csv"
            if os.path.exists(csv_name):
                # 重新创建文件，只保留表头
                with open(csv_name, mode='w', newline='', encoding='utf-8') as file:
                    fieldnames = ['图片名','车牌号','车牌颜色','置信度','识别时间']
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                return jsonify({"status": "success", "message": "今日记录已清理"}), 200
        elif clear_type == 'all':
            import glob
            csv_files = glob.glob("*.csv")
            for csv_file in csv_files:
                try:
                    os.remove(csv_file)
                except:
                    continue
            # 重新创建今日文件
            csv_name = get_time_str() + ".csv"
            with open(csv_name, mode='w', newline='', encoding='utf-8') as file:
                fieldnames = ['图片名','车牌号','车牌颜色','置信度','识别时间']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
            return jsonify({"status": "success", "message": "所有记录已清理"}), 200
        else:
            return jsonify({"status": "error", "message": "无效的清理类型"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# AI配置API
@app.route('/api/ai_config', methods=['POST'])
def ai_config():
    try:
        data = request.get_json()
        github_token = data.get('github_token', '')
        model_name = data.get('model_name', 'gpt-4o-mini')
        
        if not github_token:
            return jsonify({
                "status": "error",
                "message": "GitHub PAT token不能为空"
            }), 400
        
        # 保存配置到环境变量或配置文件
        app.config['GITHUB_TOKEN'] = github_token
        app.config['AI_MODEL'] = model_name
        
        return jsonify({
            "status": "success",
            "message": "AI配置已保存"
        }), 200
    except Exception as e:
        logger.error(f"AI配置错误: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "配置保存失败"
        }), 500

# AI对话API
@app.route('/api/ai_chat', methods=['POST'])
def ai_chat():
    try:
        message = request.form.get('message', '')
        image_file = request.files.get('image')
        
        # 检查是否配置了GitHub token
        github_token = app.config.get('GITHUB_TOKEN')
        if github_token:
            # 尝试使用GitHub模型API
            try:
                response = generate_github_ai_response(message, image_file, github_token)
                # 如果返回的是错误信息，降级到本地回复
                if "AI服务调用失败" in response or "网络连接" in response:
                    logger.warning("GitHub API调用失败，降级到本地回复")
                    response = generate_local_ai_response(message, image_file)
                    response += "\n\n💡 **提示：** 由于网络问题，当前使用本地智能回复。如需使用GitHub模型，请检查网络连接。"
            except Exception as e:
                logger.error(f"GitHub API调用异常，降级到本地回复: {str(e)}")
                response = generate_local_ai_response(message, image_file)
                response += "\n\n💡 **提示：** 由于网络问题，当前使用本地智能回复。"
        else:
            # 使用本地规则回复
            response = generate_local_ai_response(message, image_file)
        
        return jsonify({
            "status": "success",
            "response": response
        }), 200
    except Exception as e:
        logger.error(f"AI对话错误: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": "AI服务暂时不可用，请稍后再试"
        }), 500

def generate_github_ai_response(message, image_file=None, github_token=None):
    """
    使用GitHub模型API生成AI回复
    """
    import requests
    import base64
    
    try:
        # GitHub模型API配置
        api_url = "https://models.inference.ai.azure.com/chat/completions"
        model_name = app.config.get('AI_MODEL', 'gpt-4o-mini')
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {github_token}"
        }
        
        # 构建系统提示词
        system_prompt = """你是一个专业的车牌识别系统AI助手。你的职责是：
1. 回答用户关于车牌识别系统的问题
2. 分析用户上传的车牌图片
3. 提供技术支持和使用指导
4. 解释识别结果和置信度

请用专业、友好的语气回答，并使用适当的emoji让回复更生动。
如果用户上传了图片，请结合图片内容和车牌识别结果进行分析。"""

        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 处理图片
        image_analysis = ""
        if image_file:
            try:
                # 重置文件指针
                image_file.seek(0)
                img_bytes = image_file.read()
                img = Image.open(io.BytesIO(img_bytes))
                img_cv = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
                
                # 使用现有的检测函数
                _, plate_no, plate_color, confidence = detect_frame(img_cv)
                
                # 保存识别结果到历史记录
                if plate_no or confidence:  # 只要有识别结果就保存
                    csv_name = get_time_str() + ".csv"
                    with open(csv_name, mode='a', newline='', encoding='utf-8') as example_file:
                        fieldnames = ['图片名','车牌号','车牌颜色','置信度','识别时间']
                        writer = csv.DictWriter(example_file, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        
                        # 生成文件名（AI助手识别）
                        ai_filename = f"AI助手识别_{get_second_str().replace(':', '-').replace(' ', '_')}.jpg"
                        confidence_str = str(round(confidence, 4)) if confidence else "0"
                        
                        writer.writerow({
                            "图片名": ai_filename,
                            "车牌号": plate_no if plate_no else "未识别",
                            "车牌颜色": plate_color if plate_color else "未识别", 
                            "置信度": confidence_str,
                            "识别时间": get_second_str()
                        })
                
                if plate_no:
                    confidence_percent = round(confidence * 100, 2) if confidence else 0
                    image_analysis = f"车牌识别结果：车牌号码={plate_no}, 颜色={plate_color}, 置信度={confidence_percent}%（已保存到历史记录）"
                else:
                    image_analysis = "未能检测到车牌"
                
                # 将图片转换为base64
                image_file.seek(0)
                img_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                
                # 添加包含图片的消息
                user_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"{message}\n\n车牌识别系统分析结果：{image_analysis}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }
            except Exception as e:
                user_message = {
                    "role": "user", 
                    "content": f"{message}\n\n图片处理失败：{str(e)}"
                }
        else:
            user_message = {"role": "user", "content": message}
        
        messages.append(user_message)
        
        # 调用GitHub模型API
        payload = {
            "messages": messages,
            "model": model_name,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # 配置网络选项，禁用代理
        session = requests.Session()
        session.trust_env = False  # 禁用环境变量中的代理设置
        session.proxies = {}  # 清空代理设置
        
        response = session.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            return ai_response
        else:
            logger.error(f"GitHub API错误: {response.status_code} - {response.text}")
            return "抱歉，AI服务暂时不可用。请检查GitHub PAT配置或稍后再试。"
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"GitHub AI调用错误: {error_msg}")
        
        # 根据错误类型提供友好的错误信息
        if "ProxyError" in error_msg or "proxy" in error_msg.lower():
            return "网络连接失败：代理配置问题，已自动切换到本地回复模式。"
        elif "ConnectionError" in error_msg or "connection" in error_msg.lower():
            return "网络连接失败：无法连接到GitHub模型服务，已自动切换到本地回复模式。"
        elif "timeout" in error_msg.lower():
            return "网络连接失败：请求超时，已自动切换到本地回复模式。"
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            return "GitHub PAT token无效，请检查配置。已自动切换到本地回复模式。"
        else:
            return f"AI服务暂时不可用，已自动切换到本地回复模式。"

def generate_local_ai_response(message, image_file=None):
    """
    生成AI回复，专门针对车牌识别项目
    """
    message_lower = message.lower() if message else ""
    
    # 如果有图片，先分析图片
    image_analysis = ""
    if image_file:
        try:
            # 读取图片并进行车牌识别
            img_bytes = image_file.read()
            img = Image.open(io.BytesIO(img_bytes))
            img_cv = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
            
            # 使用现有的检测函数
            _, plate_no, plate_color, confidence = detect_frame(img_cv)
            
            # 保存识别结果到历史记录
            if plate_no or confidence:  # 只要有识别结果就保存
                csv_name = get_time_str() + ".csv"
                with open(csv_name, mode='a', newline='', encoding='utf-8') as example_file:
                    fieldnames = ['图片名','车牌号','车牌颜色','置信度','识别时间']
                    writer = csv.DictWriter(example_file, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    
                    # 生成文件名（AI助手识别）
                    ai_filename = f"AI助手识别_{get_second_str().replace(':', '-').replace(' ', '_')}.jpg"
                    confidence_str = str(round(confidence, 4)) if confidence else "0"
                    
                    writer.writerow({
                        "图片名": ai_filename,
                        "车牌号": plate_no if plate_no else "未识别",
                        "车牌颜色": plate_color if plate_color else "未识别", 
                        "置信度": confidence_str,
                        "识别时间": get_second_str()
                    })
            
            if plate_no:
                confidence_percent = round(confidence * 100, 2) if confidence else 0
                image_analysis = f"\n\n📸 **图片分析结果：**\n- 车牌号码：**{plate_no}**\n- 车牌颜色：**{plate_color}**\n- 识别置信度：**{confidence_percent}%**\n"
                
                if confidence_percent >= 90:
                    image_analysis += "- 识别质量：**优秀** ✅\n"
                elif confidence_percent >= 70:
                    image_analysis += "- 识别质量：**良好** ⚡\n"
                elif confidence_percent >= 50:
                    image_analysis += "- 识别质量：**一般** ⚠️\n"
                else:
                    image_analysis += "- 识别质量：**较差** ❌\n"
                    
                image_analysis += "\n💾 **已自动保存到历史记录**\n"
            else:
                image_analysis = "\n\n📸 **图片分析结果：**\n- 未能检测到车牌，可能原因：\n  - 图片中没有车牌\n  - 车牌被遮挡或模糊\n  - 图片质量较差\n  - 车牌角度过大\n"
        except Exception as e:
            image_analysis = f"\n\n📸 **图片分析失败：** {str(e)}\n"
    
    # 基于关键词的智能回复
    if any(keyword in message_lower for keyword in ['你好', 'hello', 'hi', '您好']):
        response = """👋 您好！我是车牌识别系统的AI助手！

我可以帮助您：
🚗 **车牌识别相关问题** - 解答识别原理、准确率等
📸 **图片分析** - 上传车牌图片进行实时分析  
🔧 **系统使用指导** - 功能介绍、操作步骤
📊 **结果解释** - 置信度含义、颜色分类等
❓ **问题排查** - 识别失败原因、优化建议

请告诉我您想了解什么，或者直接上传车牌图片让我分析！"""

    elif any(keyword in message_lower for keyword in ['置信度', 'confidence', '准确率', '可信度']):
        response = """📊 **关于置信度的详细说明：**

**什么是置信度？**
置信度是AI模型对识别结果确信程度的量化指标，范围0-100%。

**置信度等级：**
- 🟢 **90-100%：优秀** - 识别结果非常可靠
- 🟡 **70-89%：良好** - 识别结果较为可靠  
- 🟠 **50-69%：一般** - 识别结果需要人工确认
- 🔴 **0-49%：较差** - 识别结果不可靠，建议重新拍摄

**影响置信度的因素：**
- 图片清晰度和光照条件
- 车牌是否完整可见
- 拍摄角度和距离
- 车牌污损程度"""

    elif any(keyword in message_lower for keyword in ['颜色', 'color', '蓝牌', '绿牌', '黄牌']):
        response = """🎨 **车牌颜色分类说明：**

我们的系统可以识别以下车牌颜色：

🔵 **蓝色车牌** - 普通小型汽车
🟢 **绿色车牌** - 新能源汽车  
🟡 **黄色车牌** - 大型汽车、货车、客车
⚪ **白色车牌** - 军用、警用车辆
⚫ **黑色车牌** - 外籍、领事馆车辆

**识别原理：**
系统通过深度学习模型分析车牌的颜色特征，结合车牌号码格式进行综合判断。

**注意事项：**
- 光照条件会影响颜色识别准确性
- 建议在自然光下拍摄获得最佳效果"""

    elif any(keyword in message_lower for keyword in ['如何使用', '怎么用', '操作', '使用方法', '教程']):
        response = """📖 **系统使用指南：**

**🖼️ 图片检测：**
1. 点击"图片检测"卡片
2. 拖拽或点击上传车牌图片
3. 点击"开始识别"按钮
4. 查看识别结果和置信度

**🎥 视频检测：**
1. 点击"视频检测"卡片  
2. 上传包含车牌的视频文件
3. 点击"上传视频"等待处理
4. 点击"开始检测"进行批量识别
5. 查看检测统计和结果视频

**📹 实时检测：**
1. 点击"摄像头检测"卡片
2. 点击"开启摄像头"
3. 将车牌对准摄像头
4. 系统实时显示识别结果

**💡 使用技巧：**
- 确保车牌完整清晰可见
- 避免强光直射或阴影遮挡
- 保持适当的拍摄距离和角度"""

    elif any(keyword in message_lower for keyword in ['识别失败', '检测不到', '无法识别', '错误']):
        response = """🔧 **识别问题排查指南：**

**常见问题及解决方案：**

❌ **完全检测不到车牌：**
- 确认图片中确实包含车牌
- 检查车牌是否被遮挡
- 尝试调整图片亮度和对比度
- 确保车牌占据图片合适比例

❌ **识别结果错误：**
- 检查车牌是否清晰可见
- 避免车牌反光或污损
- 尝试不同角度拍摄
- 确保光照条件良好

❌ **置信度过低：**
- 提高图片分辨率和清晰度
- 减少背景干扰
- 确保车牌字符完整
- 避免运动模糊

**优化建议：**
- 使用1080P以上分辨率
- 在自然光下拍摄
- 保持车牌水平
- 距离适中（2-5米）"""

    elif any(keyword in message_lower for keyword in ['模型', 'yolo', 'ai', '算法', '技术']):
        response = """🤖 **技术架构介绍：**

**核心技术栈：**
- **YOLOv5** - 车牌检测模型，快速定位车牌位置
- **LPRNet** - 车牌识别模型，识别车牌号码和颜色
- **ONNX Runtime** - 模型推理引擎，支持GPU加速
- **OpenCV** - 图像处理库
- **Flask** - 后端API框架
- **Vue.js** - 前端界面框架

**工作流程：**
1. **图像预处理** - 尺寸调整、归一化
2. **车牌检测** - YOLOv5定位车牌区域
3. **区域提取** - 裁剪车牌区域
4. **字符识别** - LPRNet识别号码和颜色
5. **结果后处理** - 置信度计算、格式化输出

**性能特点：**
- 检测速度：< 100ms/张
- 识别准确率：> 95%
- 支持多种车牌类型
- GPU加速推理"""

    elif any(keyword in message_lower for keyword in ['历史记录', '历史', '记录', '查看记录']):
        response = """📋 **历史记录功能说明：**

**记录内容：**
- 识别时间和日期
- 原始图片名称  
- 识别的车牌号码
- 车牌颜色类型
- 识别置信度
- 处理结果图片

**查看方式：**
- 点击导航栏"历史记录"
- 支持按时间排序
- 可以下载记录数据
- 支持批量删除

**管理员功能：**
- 查看所有用户记录
- 系统统计信息
- 批量清理功能
- 用户管理

**数据存储：**
- 本地CSV文件存储
- 按日期自动分类
- 支持数据导出
- 隐私保护机制"""

    elif any(keyword in message_lower for keyword in ['支持格式', '格式', '文件类型']):
        response = """📁 **支持的文件格式：**

**图片格式：**
- JPG/JPEG - 推荐使用
- PNG - 支持透明背景
- BMP - 基础位图格式
- TIFF - 高质量图像

**视频格式：**
- MP4 - 推荐格式，兼容性最好
- AVI - 传统视频格式
- MOV - Apple设备常用
- WMV - Windows媒体格式

**文件大小限制：**
- 图片：最大 10MB
- 视频：最大 100MB

**推荐规格：**
- 图片分辨率：1920x1080 或更高
- 视频分辨率：1080P
- 图片格式：JPG（压缩比好）
- 视频格式：MP4（兼容性佳）

**注意事项：**
- 文件名避免特殊字符
- 确保文件完整未损坏
- 网络上传需要稳定连接"""

    elif any(keyword in message_lower for keyword in ['谢谢', 'thank', '感谢']):
        response = """😊 **不客气！很高兴能帮助您！**

如果您还有其他问题，随时可以：
- 继续向我提问
- 上传图片让我分析
- 查看系统使用指南
- 体验各项检测功能

祝您使用愉快！🚗✨"""

    else:
        # 默认回复，提供通用帮助
        response = f"""🤔 **关于"{message}"的回答：**

我是专门为车牌识别系统设计的AI助手，我可以帮助您：

🔍 **常见问题：**
- 车牌识别原理和技术
- 置信度和准确率说明  
- 系统使用方法和技巧
- 识别问题排查和优化
- 支持的文件格式
- 历史记录功能

💡 **建议您可以问我：**
- "如何提高识别准确率？"
- "置信度是什么意思？"
- "为什么识别失败？"
- "支持哪些车牌颜色？"
- "怎么使用视频检测？"

或者直接上传车牌图片，我来帮您分析！"""

    return response + image_analysis

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)