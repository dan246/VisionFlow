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
        "annotators": {  
            "box_annotator": {
                "type": "BoxAnnotator",
                "thickness": 2
                # 如果 BoxAnnotator 支持 color 参数，可以在这里指定
                # "color": (255, 0, 0)
            },
            "label_annotator": {
                "type": "LabelAnnotator",
                "text_position": "TOP_CENTER",
                "text_thickness": 2,
                "text_scale": 1
            }
        }
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
        "annotators": {
            "box_annotator": {
                "type": "RoundBoxAnnotator",
                "thickness": 2,
                "color": (0, 255, 0)  # 綠色
            },
            "label_annotator": {
                "type": "LabelAnnotator",
                "text_position": "BOTTOM_CENTER",
                "text_thickness": 2,
                "text_scale": 1
            },
        }
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
        "annotators": {
            "box_annotator": {
                "type": "BoxCornerAnnotator",
                "thickness": 2,
                "color": (0, 0, 255)  # 藍色
            },
            "label_annotator": {
                "type": "LabelAnnotator",
                "text_position": "TOP_RIGHT",
                "text_thickness": 2,
                "text_scale": 1
            },
        }
    },
}
