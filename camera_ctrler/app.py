from flask import Flask, request, jsonify, send_file, render_template, Response
from flask_restx import Api, Resource, fields
from redis_utils import init_redis, CameraSnapFetcher, get_all_camera_status
from camera_manager import CameraManager
import threading
import time
from datetime import datetime
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
# 允取特定網域打入
# allowed_origins = ["https://pytest.intemotech.com"]

# cors = CORS(app, resources={
#     r"/*": {"origins": allowed_origins}
# })

# 初始化 Redis
r = init_redis()

manager = CameraManager()
manager.run()

camera_model = api.model('Camera', {
    'camera_id': fields.String(required=True, description='The camera identifier'),
    'url': fields.String(required=True, description='The URL of the camera stream')
})

camera_ids_model = api.model('CameraIds', {
    'camera_ids': fields.List(fields.String, required=True, description='List of camera identifiers')
})


polygon_model = api.model('Polygon', {
    'points': fields.List(fields.Nested(api.model('Point', {
        'x': fields.Float(required=True, description='X coordinate of the point'),
        'y': fields.Float(required=True, description='Y coordinate of the point'),
    }))),
    'camera_id': fields.String(required=True, description='Camera ID associated with this polygon')
})


@api.route('/camera_status')
class CameraStatus(Resource):
    def get(self):
        status = get_all_camera_status(r)
        return status, 200

@app.route('/get_snapshot/<camera_id>')
def get_latest_frame(camera_id):
    image_data = r.get(f'camera_{camera_id}_latest_frame')
    if image_data:
        return Response(image_data, mimetype='image/jpeg')
    else:
        return send_file('no_single.jpg', mimetype='image/jpeg')

@app.route('/image/<path:image_path>')
def get_image(image_path):
    try:
        return send_file(image_path, mimetype='image/jpeg')
    except FileNotFoundError:
        return send_file('no_single.jpg', mimetype='image/jpeg')

def generate_frames(camera_id):
    while True:
        frame_key = f'camera_{camera_id}_latest_frame'
        frame_data = r.get(frame_key)
        if frame_data:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        time.sleep(0.1)


# def generate_recognized_frames(camera_id):
#     while True:
#         frame_key = f'camera_{camera_id}_boxed_image'
#         frame_data = r.get(frame_key)
#         if frame_data:
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
#         time.sleep(0.1)

def generate_recognized_frames(camera_id):
    polygons_key = f'polygons_{camera_id}'  # 多邊形存儲鍵

    while True:
        frame_key = f'camera_{camera_id}_boxed_image'
        frame_data = r.get(frame_key)
        
        if frame_data:
            # 將影像數據轉換成 PIL 影像格式
            image = Image.open(io.BytesIO(frame_data)).convert("RGBA")
            overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))  # 建立一個空的透明圖層
            draw = ImageDraw.Draw(overlay)

            # 加載並繪製多邊形
            for key in r.scan_iter(f"{polygons_key}:*"):
                polygon_data = r.get(key)
                if polygon_data:
                    polygon = json.loads(polygon_data)
                    scaled_polygon = [(point['x'], point['y']) for point in polygon]
                    
                    # 使用白色邊框，透明填充多邊形
                    draw.polygon(scaled_polygon, outline="white", fill=(255, 255, 255, 80))  # 80 表示透明度

            # 合併原影像與多邊形覆蓋圖層
            combined_image = Image.alpha_composite(image, overlay).convert("RGB")

            # 將繪製了多邊形的影像重新編碼為JPEG格式
            img_io = io.BytesIO()
            combined_image.save(img_io, 'JPEG')
            img_io.seek(0)

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_io.getvalue() + b'\r\n')
        
        time.sleep(0.1)

# 辨識串流路由( 經由 redis )
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
    

# 顯示圖片 GET 方法
@app.route('/showimage/<path:image_path>', methods=['GET'])
def show_image_get(image_path):
    # 解碼 URL 的中文路徑
    image_path = unquote(image_path)
    
    # 移除前綴
    prefix = 'saved_images/annotated_images/'
    if image_path.startswith(prefix):
        image_path = image_path[len(prefix):]
    
    # 設定基礎目錄
    base_dir = os.path.join(app.root_path, 'saved_images', 'annotated_images')
    
    # 組合完整的路徑
    image_full_path = safe_join(base_dir, image_path)
    
    print(f"Requested image path: {image_full_path}")
    
    # 確認圖片存在
    if not os.path.exists(image_full_path):
        print(f"Image not found at path: {image_full_path}")
        return jsonify({'error': 'Image not found', 'path': image_full_path}), 404

    try:
        # 返回圖片
        return send_file(image_full_path, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 處理多邊形的路由
@app.route('/rectangles/<ID>', methods=['POST', 'GET', 'DELETE'])
def handle_polygons(ID):
    polygons_key = f'polygons_{ID}'

    if request.method == 'POST':
        # 接收前端傳遞的多邊形資料
        polygons = request.get_json()
        logging.info(f"Received polygons: {polygons}")  # 日誌輸出接收到的多邊形

        if not polygons:
            return jsonify(message="No polygons received"), 400

        # 刪除現有的多邊形資料
        for key in r.scan_iter(f"{polygons_key}:*"):
            r.delete(key)
        # 儲存新的多邊形資料
        for idx, polygon in enumerate(polygons):
            key = f"{polygons_key}:{idx}"
            r.set(key, json.dumps(polygon))
            logging.info(f"Saved polygon {key}: {polygon}")
        return jsonify(message="多邊形已儲存"), 200

    elif request.method == 'GET':
        # 返回所有多邊形的點數據
        polygons = []
        for key in r.scan_iter(f"{polygons_key}:*"):
            polygon_data = r.get(key)
            if polygon_data:
                polygon = json.loads(polygon_data)
                polygons.append(polygon)
                logging.info(f"Loaded polygon {key}: {polygon}")
        return jsonify(polygons), 200

    elif request.method == 'DELETE':
        for key in r.scan_iter(f"{polygons_key}:*"):
            r.delete(key)
        return jsonify(message="所有多邊形已清除"), 200

# 顯示 mask 的路由
@app.route('/mask/<ID>', methods=['GET'])
def generate_mask(ID):
    # 創建遮罩圖像
    mask_width = 1920  # 根據需要設置遮罩寬度
    mask_height = 1080  # 根據需要設置遮罩高度
    mask_image = Image.new("L", (mask_width, mask_height), 0)  # 黑色背景
    draw = ImageDraw.Draw(mask_image)

    polygons_key = f'polygons_{ID}'
    for key in r.scan_iter(f"{polygons_key}:*"):
        polygon_data = r.get(key)
        if polygon_data:
            polygon = json.loads(polygon_data)
            scaled_polygon = [(int(point['x']), int(point['y'])) for point in polygon]
            draw.polygon(scaled_polygon, outline=255, fill=255)  # 白色填充

    mask_io = io.BytesIO()
    mask_image.save(mask_io, "PNG")
    mask_io.seek(0)
    return send_file(mask_io, mimetype="image/png")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)
    app.run(host='0.0.0.0', port=5000)
    # app.run()
