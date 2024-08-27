from huggingfaceapi import DatasetManager
import os
import time
import threading
from huggingfaceapi import DatasetManager
import os
import time

class AutoUpdater(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        TOKEN = os.getenv("TOKEN")
        DATASETNAME = os.getenv("DATASETNAME")
        if TOKEN is None:
            raise ValueError("Error: TOKEN environment variable not set.")
        while self.daemon:
            try:
                # 格式化日期時間
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                print("開始更新")
                manager = DatasetManager(TOKEN, base_image_dir=f'./saved_images/')
                manager.upload_dataset(DATASETNAME, private=False)
                    
                print("更新完成")
                time.sleep(60*60*24) # 24 hours
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60*60*24) # 24 hours

# Create and start the AutoUpdater thread
if __name__ == "__main__":
    auto_updater = AutoUpdater()
    auto_updater.start()
    auto_updater.join()
