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

def setup_camera_manager():
    manager = CameraManager()
    manager.run()
    timer = threading.Timer(1, setup_camera_manager)
    timer.start()

setup_camera_manager()

camera_model = api.model('Camera', {
    'camera_id': fields.String(required=True, description='The camera identifier'),
    'url': fields.String(required=True, description='The URL of the camera stream')
})

camera_ids_model = api.model('CameraIds', {
    'camera_ids': fields.List(fields.String, required=True, description='List of camera identifiers')
})

rect_model = api.model('Rectangle', {
    'x': fields.Float(required=True, description='X coordinate of the rectangle'),
    'y': fields.Float(required=True, description='Y coordinate of the rectangle'),
    'width': fields.Float(required=True, description='Width of the rectangle'),
    'height': fields.Float(required=True, description='Height of the rectangle'),
    'camera_id': fields.String(required=True, description='Camera ID associated with this rectangle')
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


def generate_recognized_frames(camera_id):
    while True:
        frame_key = f'camera_{camera_id}_boxed_image'
        frame_data = r.get(frame_key)
        if frame_data:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        time.sleep(0.1)

@app.route('/recognized_stream/<ID>')
def recognized_stream(ID):
    return Response(generate_recognized_frames(ID), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_stream/<int:ID>')
def get_stream(ID):
    return Response(generate_frames(ID), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/snapshot_ui/<ID>')
def snapshot_ui(ID):
    image_key = f'camera_{ID}_latest_frame'
    image_data = r.get(image_key)
    if image_data:
        try:
            image = Image.open(io.BytesIO(image_data))
            draw = ImageDraw.Draw(image)
            rects_key = f'rectangles_{ID}'
            for key in r.scan_iter(f"{rects_key}:*"):
                rect_data = r.hgetall(key)
                rect = [int(float(v.decode())) for v in rect_data.values()]
                # 確保 x1 >= x0 和 y1 >= y0
                if rect[2] < 0:
                    rect[0] += rect[2]
                    rect[2] = abs(rect[2])
                if rect[3] < 0:
                    rect[1] += rect[3]
                    rect[3] = abs(rect[3])
                draw.rectangle([rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]], outline='red', width=2)
            
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            encoded_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

            # 確保這裡被執行
            print("Rendering template with image data...")
            return render_template('snapshot_ui.html', camera_id=ID, image_data=encoded_image)

        except Exception as e:
            print(f"Error processing image for {ID}: {e}")
            return send_file('no_single.jpg', mimetype='image/jpeg')
    else:
        return send_file('no_single.jpg', mimetype='image/jpeg')

@app.route('/rectangles/<ID>', methods=['POST', 'GET', 'DELETE'])
def handle_rectangles(ID):
    camera_status = r.get(f'camera_{ID}_status')
    if camera_status is None:
        return jsonify(message="無效的 ID"), 404
    rects_key = f'rectangles_{ID}'
    if request.method == 'POST':
        rects = request.get_json()
        for idx, rect in enumerate(rects):
            r.hset(f"{rects_key}:{idx}", mapping={k: str(v) for k, v in rect.items()})
        return jsonify(message="矩形已儲存"), 200
    elif request.method == 'GET':
        rects = []
        for key in r.scan_iter(f"{rects_key}:*"):
            rect_data = r.hgetall(key)
            rect = {k.decode(): int(float(v.decode())) for k, v in rect_data.items()}
            rects.append(rect)
        return jsonify(rects)
    elif request.method == 'DELETE':
        for key in r.scan_iter(f"{rects_key}:*"):
            r.delete(key)
        return jsonify(message="所有矩形已清除"), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=15440)
