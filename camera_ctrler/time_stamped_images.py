import os
from datetime import datetime, timedelta

class TimeStampedImages:
    def __init__(self, folder_path):
        self.folder_path = folder_path
    
    def find_images_in_range(self, start_timestamp, end_timestamp):
        # 將傳入的時間搓轉換為 datetime 對象
        start = datetime.fromtimestamp(start_timestamp)
        end = datetime.fromtimestamp(end_timestamp)
        
        matched_files = []
        
        # 遍歷資料夾中的所有子資料夾
        for item in os.listdir(self.folder_path):
            try:
                for foldername in os.listdir(self.folder_path+"/"+item):
                    # 轉換子資料夾名稱，假設格式為 'YYYYMMDD_HH'
                    folder_datetime = datetime.strptime(item+"_"+foldername, "%Y%m%d_%H")
                    # 檢查資料夾的時間是否在指定的範圍內
                    if start  - timedelta(hours=1) <= folder_datetime <= end + timedelta(hours=1):  # 加一小時來包含範圍內的整小時
                        # 遍歷該子資料夾中的所有檔案
                        full_folder_path = os.path.join(self.folder_path, item,foldername)
                        for filename in os.listdir(full_folder_path):
                            if filename.endswith('.jpg'):
                                if start <= datetime.strptime(filename, "%Y%m%d%H%M%S.jpg") <= end:
                                    file_path = os.path.join(full_folder_path, filename)
                                    matched_files.append(file_path)
            except ValueError:
                # 如果子資料夾名稱不是日期時間格式，則忽略
                continue
        
        return matched_files

# # # 使用範例
# folder_path = 'camera_100/image/7'
# start_timestamp = float("1714055407.8254943") - 15
# end_timestamp = float("1714055407.8254943") + 15

# tsi = TimeStampedImages(folder_path)
# image_paths = tsi.find_images_in_range(start_timestamp, end_timestamp)

# starttime = '2024-04-25 15:09:10'
# endtime = "2024-04-25 15:10:00"
# start_timestamp = datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S").timestamp()
# end_timestamp = datetime.strptime(endtime, "%Y-%m-%d %H:%M:%S").timestamp()
# filelist = tsi.find_images_in_range(start_timestamp, end_timestamp)
# len(filelist)