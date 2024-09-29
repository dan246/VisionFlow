# 定義模型的配置參數
MODEL_CONFIG = {
    "model1": {
        "path": ["https://example.com/path/to/model1.pt"],
        "conf": 0.5,  # 整體 conf
        "label_conf": {  # 針對某些 label 的特殊 conf 設定
            "Label A": 0.7,
            "Label B": 0.6,
        }
    },
    "model2": {
        "path": ["https://example.com/path/to/model2.pt"],
        "conf": 0.5,
        "label_conf": {
            "Label A": 0.7,
            "Label B": 0.6,
        }
    },
    "model3": {
        "path": ["https://example.com/path/to/model3.pt"],
        "conf": 0.5,
        "label_conf": {
            "Label A": 0.7,
            "Label B": 0.6,
        }
    }
}
