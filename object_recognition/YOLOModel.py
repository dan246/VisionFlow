import os
import hashlib
from urllib import request
from pathlib import Path
from ultralytics import YOLO

class YOLOModel:
    def __init__(self, model_urls):
        self.models = self._download_and_load_models(model_urls)
        self.model_names = [model.names for model in self.models]

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
                image_results.append(data)
            results.append(image_results)
        return results
