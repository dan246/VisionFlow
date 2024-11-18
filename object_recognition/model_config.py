# model_config.py

# 定義模型的配置參數
MODEL_CONFIG = {
    "model1": {
        "path": ["yolo11n.pt"],  
        "conf": 0.5,  
        "label_conf": {  
            "person": 0.7,
            "bicycle": 0.6,
            "car": 0.6,
            "dog": 0.7,
        },
    },
    "model2": {
        "path": ["model/yolo11n.pt"],  
        "conf": 0.5,
        "label_conf": {
            "cat": 0.7,
            "laptop": 0.6,
            "cell phone": 0.6,
            "chair": 0.7,
        },
    },
    "model3": {
        "path": ["model/yolo11n.pt"], 
        "conf": 0.5,
        "label_conf": {
            "bottle": 0.7,
            "cup": 0.6,
            "fork": 0.6,
            "knife": 0.7,
        },
    },
}