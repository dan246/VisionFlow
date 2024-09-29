import os
import hashlib
from urllib import request
from pathlib import Path
from ultralytics import YOLO
import logging

class YOLOModel:
    def __init__(self, model_urls, default_conf=0.5, label_conf=None):
        self.logger = logging.getLogger('YOLOModel')
        self.models = self._download_and_load_models(model_urls)
        self.model_names = [model.names for model in self.models]
        self.default_conf = default_conf
        self.label_conf = label_conf if label_conf else {}

    def _download_and_load_models(self, model_urls):
        models = []
        for model_url in model_urls:
            model_path = self._download_model(model_url)
            model = self._load_model(model_path)
            models.append(model)
        return models

    def _download_model(self, model_url):
        # 創建存儲模型的臨時目錄
        tmp_dir = Path("tmp")
        tmp_dir.mkdir(exist_ok=True)

        # 通過 URL 生成唯一的文件名
        filename = hashlib.md5(model_url.encode('utf-8')).hexdigest() + ".pt"
        file_path = tmp_dir / filename

        # 如果文件不存在，則下載
        if not file_path.exists():
            print("下載模型...")
            request.urlretrieve(model_url, file_path)
        else:
            print("模型已存在，不需重新下載。")

        return file_path

    def _load_model(self, model_path):
        # 加載模型
        print("載入模型...")
        return YOLO(model_path)

    def predict(self, images):
        results = []
        for image in images:
            image_results = []
            for model in self.models:
                data = model(image)
                filtered_data = self._filter_predictions(data)
                image_results.append(filtered_data)
            results.append(image_results)
        return results

    def _filter_predictions(self, predictions):
        # 遍歷每個預測結果，應用自定義的 conf 過濾
        filtered_predictions = []
        for pred in predictions:
            filtered_boxes = []
            for box in pred.boxes:
                class_id = int(box.cls[0])  # 假設每個框只有一個 class
                conf = box.conf[0]
                label = self.model_names[0][class_id]  # 假設所有模型共享相同的類別名稱

                # 檢查是否有針對該 label 的自定義 conf
                label_specific_conf = self.label_conf.get(label, self.default_conf)
                
                # 如果預測框的信心值大於等於指定的門檻，則保留該框
                if conf >= label_specific_conf:
                    filtered_boxes.append(box)
            
            # 如果有符合條件的框，將其加入篩選後的結果
            if filtered_boxes:
                pred.boxes = filtered_boxes
                filtered_predictions.append(pred)

        return filtered_predictions
