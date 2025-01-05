from flask import Flask, request, jsonify, send_file, render_template, Response
from flask_restx import Api, Resource, fields
from redis_utils import init_redis, CameraSnapFetcher, get_all_camera_status
from camera_manager import CameraManager
import threading
import time
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw
import base64
import io
from flask_cors import CORS
import os
from urllib.parse import unquote
from werkzeug.utils import safe_join
import logging
import sys
import json

app = Flask(__name__)
api = Api(app)
CORS(app)
# 初始化 Redis
r = init_redis()

manager = CameraManager()
manager.run()


@api.route('/camera_status')
class CameraStatus(Resource):
    def get(self):
        status = get_all_camera_status(r)
        return status, 200

# 獲取最新快照
@app.route('/get_snapshot/<camera_id>')
def get_latest_frame(camera_id):
    image_data = r.get(f'camera_{camera_id}_latest_frame')
    if image_data:
        return Response(image_data, mimetype='image/jpeg')
    else:
        return send_file('no_single.jpg', mimetype='image/jpeg')

# 顯示圖片
@app.route('/showimage/<path:image_path>')
def get_image(image_path):
    try:
        return send_file(image_path, mimetype='image/jpeg')
    except FileNotFoundError:
        return send_file('no_single.jpg', mimetype='image/jpeg')

# 生成串流畫面
def generate_frames(camera_id):
    while True:
        frame_key = f'camera_{camera_id}_latest_frame'
        frame_data = r.get(frame_key)
        if frame_data:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        time.sleep(0.1)

def generate_recognized_frames(camera_id):
    polygons_key = f'polygons_{camera_id}'  # 多邊形存儲鍵
    start_time_key = f'start_time_{camera_id}'  # 開始時間存儲鍵
    end_time_key = f'end_time_{camera_id}'      # 結束時間存儲鍵

    while True:
        frame_key = f'camera_{camera_id}_boxed_image'
        frame_data = r.get(frame_key)
        
        if frame_data:
            # 將影像數據轉換成 PIL 影像格式
            image = Image.open(io.BytesIO(frame_data)).convert("RGBA")
            overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))  # 建立一個空的透明圖層
            draw = ImageDraw.Draw(overlay)

            # 獲取當前時間（當地時間）
            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute

            # 獲取設定的開始和結束時間
            start_time_str = r.get(start_time_key)
            end_time_str = r.get(end_time_key)

            in_time_interval = False
            if start_time_str and end_time_str:
                start_hour, start_minute = map(int, start_time_str.decode('utf-8').split(':'))
                end_hour, end_minute = map(int, end_time_str.decode('utf-8').split(':'))

                # 檢查當前時間是否在設定的時間區段內
                start_total_minutes = start_hour * 60 + start_minute
                end_total_minutes = end_hour * 60 + end_minute
                current_total_minutes = current_hour * 60 + current_minute

                if start_total_minutes <= current_total_minutes <= end_total_minutes:
                    in_time_interval = True
                else:
                    in_time_interval = False
            else:
                # 如果沒有設定時間區段，則視為不限制時間
                in_time_interval = True

            # 加載並繪製多邊形
            for key in r.scan_iter(f"{polygons_key}:*"):
                polygon_data = r.get(key)
                if polygon_data:
                    polygon = json.loads(polygon_data)
                    scaled_polygon = [(point['x'], point['y']) for point in polygon['points']]
                    # 使用白色邊框，透明填充多邊形
                    draw.polygon(scaled_polygon, outline="white", fill=(255, 255, 255, 80))  # 80 表示透明度

            # 如果在時間區段內，對整個影像進行處理（例如，加上半透明覆蓋）
            if in_time_interval:
                pass  # 如果需要，可以在這裡進行額外的處理
            else:
                # 如果不在時間區段內，可能需要對影像進行不同的處理
                time_overlay = Image.new("RGBA", image.size, (0, 0, 0, 180))  # 深色半透明覆蓋
                overlay = Image.alpha_composite(overlay, time_overlay)

            # 合併原影像與覆蓋圖層
            combined_image = Image.alpha_composite(image, overlay).convert("RGB")

            # 將繪製了多邊形的影像重新編碼為JPEG格式
            img_io = io.BytesIO()
            combined_image.save(img_io, 'JPEG')
            img_io.seek(0)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_io.getvalue() + b'\r\n')
        
        time.sleep(0.1)

# 辨識串流路由
@app.route('/recognized_stream/<ID>')
def recognized_stream(ID):
    return Response(generate_recognized_frames(ID), mimetype='multipart/x-mixed-replace; boundary=frame')

# 串流路由
@app.route('/get_stream/<int:ID>')
def get_stream(ID):
    return Response(generate_frames(ID), mimetype='multipart/x-mixed-replace; boundary=frame')

# 快照 UI 路由
@app.route('/snapshot_ui/<ID>')
def snapshot_ui(ID):
    image_key = f'camera_{ID}_latest_frame'
    image_data = r.get(image_key)
    if image_data:
        # 將圖片編碼為 Base64，傳遞給模板
        encoded_image = base64.b64encode(image_data).decode('utf-8')
        return render_template('snapshot_ui.html', camera_id=ID, image_data=encoded_image)
    else:
        return send_file('no_single.jpg', mimetype='image/jpeg')

# 處理多邊形的路由
@app.route('/rectangles/<ID>', methods=['POST', 'GET', 'DELETE'])
def handle_polygons(ID):
    polygons_key = f'polygons_{ID}'

    if request.method == 'POST':
        polygons = request.get_json()
        logging.info(f"Received polygons: {polygons}")

        if not polygons:
            return jsonify(message="未接收到多邊形資料"), 400

        # 清除既有多邊形
        for key in r.scan_iter(f"{polygons_key}:*"):
            r.delete(key)

        # 儲存新的多邊形資料(包含duration)
        for idx, polygon_data in enumerate(polygons):
            # 新增 duration 欄位的處理，若無則預設為0
            duration = polygon_data.get("duration", 0)
            key = f"{polygons_key}:{idx}"
            r.set(key, json.dumps({
                "points": polygon_data["points"],
                "name": polygon_data.get("name", f"未命名區域{idx + 1}"),
                "color": polygon_data.get("color", "#00ff00"),
                "duration": duration
            }))
            logging.info(f"Saved polygon {key}: {polygon_data}")

        return jsonify(message="多邊形已儲存"), 200

    elif request.method == 'GET':
        polygons = []
        for key in r.scan_iter(f"{polygons_key}:*"):
            polygon_data = r.get(key)
            if polygon_data:
                polygon = json.loads(polygon_data)
                polygons.append({
                    "points": polygon["points"],
                    "name": polygon.get("name", "Unnamed"),
                    "color": polygon.get("color", "#00ff00"),
                    "duration": polygon.get("duration", 0) # 從redis資料中取出duration
                })
                logging.info(f"Loaded polygon {key}: {polygon}")

        return jsonify(polygons), 200

    elif request.method == 'DELETE':
        for key in r.scan_iter(f"{polygons_key}:*"):
            r.delete(key)
        return jsonify(message="所有多邊形已清除"), 200
    

# 處理時間區段的路由
@app.route('/time_intervals/<ID>', methods=['POST', 'GET', 'DELETE'])
def handle_time_intervals(ID):
    start_time_key = f'start_time_{ID}'
    end_time_key = f'end_time_{ID}'

    if request.method == 'POST':
        # 接收前端傳遞的時間資料
        data = request.get_json()
        logging.info(f"Received time data: {data}")

        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if not start_time or not end_time:
            return jsonify(message="未接收到完整的時間資料"), 400

        # 儲存新的時間資料
        r.set(start_time_key, start_time)
        r.set(end_time_key, end_time)
        logging.info(f"Saved start_time: {start_time}, end_time: {end_time}")
        return jsonify(message="時間區段已儲存"), 200

    elif request.method == 'GET':
        # 返回時間資料
        start_time = r.get(start_time_key)
        end_time = r.get(end_time_key)

        if start_time and end_time:
            data = {
                'start_time': start_time.decode('utf-8'),
                'end_time': end_time.decode('utf-8')
            }
            return jsonify(data), 200
        else:
            return jsonify(message="未設定時間區段"), 404

    elif request.method == 'DELETE':
        r.delete(start_time_key)
        r.delete(end_time_key)
        return jsonify(message="時間區段已清除"), 200

@app.route('/mask/<ID>', methods=['GET'])
def generate_mask(ID):
    # 創建遮罩圖像
    mask_width = 1920  # 根據需要設置遮罩寬度
    mask_height = 1080  # 根據需要設置遮罩高度
    mask_image = Image.new("L", (mask_width, mask_height), 0)  # 黑色背景
    draw = ImageDraw.Draw(mask_image)

    polygons_key = f'polygons_{ID}'
    polygons_info = []  # 用於存儲多邊形資訊 (名字、坐標、duration)

    for key in r.scan_iter(f"{polygons_key}:*"):
        polygon_data = r.get(key)
        if polygon_data:
            polygon = json.loads(polygon_data)
            name = polygon.get('name', 'Unnamed')  # 取得名字，預設為 'Unnamed'
            duration = polygon.get('duration', 0)  # 取得 duration，預設為0
            scaled_polygon = [(int(point['x']), int(point['y'])) for point in polygon['points']]
            draw.polygon(scaled_polygon, outline=255, fill=255)  # 白色填充

            # 添加多邊形區域的名字到遮罩中(非必須，可依需求)
            centroid_x = sum(x for x, y in scaled_polygon) // len(scaled_polygon)
            centroid_y = sum(y for x, y in scaled_polygon) // len(scaled_polygon)
            draw.text((centroid_x, centroid_y), name, fill=255)

            # 儲存多邊形資訊，增加duration欄位
            polygons_info.append({
                "name": name,
                "points": scaled_polygon,
                "duration": duration
            })

    # 將遮罩圖片保存到記憶體
    mask_io = io.BytesIO()
    mask_image.save(mask_io, "PNG")
    mask_io.seek(0)

    # 將圖片和多邊形資訊封裝成 JSON 回應
    response = {
        "image_url": f"http://192.168.53.88:15440/get_mask_image/{ID}",  # 提供圖片的 URL 地址
        "polygons_info": polygons_info
    }

    return jsonify(response)  # 返回 JSON 資料


@app.route('/get_mask_image/<ID>', methods=['GET'])
def get_mask_image(ID):
    # 重新創建遮罩圖像
    mask_width = 1920  # 根據需要設置遮罩寬度
    mask_height = 1080  # 根據需要設置遮罩高度
    mask_image = Image.new("L", (mask_width, mask_height), 0)  # 黑色背景
    draw = ImageDraw.Draw(mask_image)

    polygons_key = f'polygons_{ID}'
    for key in r.scan_iter(f"{polygons_key}:*"):
        polygon_data = r.get(key)
        if polygon_data:
            polygon = json.loads(polygon_data)
            scaled_polygon = [(int(point['x']), int(point['y'])) for point in polygon['points']]
            draw.polygon(scaled_polygon, outline=255, fill=255)  # 白色填充

    # 將遮罩圖片保存到記憶體
    mask_io = io.BytesIO()
    mask_image.save(mask_io, "PNG")
    mask_io.seek(0)

    return send_file(mask_io, mimetype="image/png")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
    app.run(host='0.0.0.0', port=5000)