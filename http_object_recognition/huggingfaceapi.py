import os
import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset, Image, Features, Value
from huggingface_hub import HfApi, HfFolder, Repository

class DatasetManager:
    def __init__(self, token, base_image_dir='./saved_images/'):
        self.token = token
        HfFolder.save_token(token)
        self.api = HfApi()
        self.base_image_dir = base_image_dir
        
    def download_dataset(self, dataset_name, data_dir="default", split='train'):
        dataset = load_dataset(dataset_name, data_dir, split=split, cache_dir='./cache')
        
        for i in range(len(dataset)):
            sample = dataset[i]
            image_data = sample['image']
            path = sample['path']
            base_filename = path.split('/')[-1].split('.')[0]
            image_save_path = os.path.join(self.base_image_dir, 'annotated_images', f'{base_filename}.jpg')
            
            if os.path.exists(image_save_path):
                print(f"Error: File already exists. filename: {base_filename}")
                continue
            
            os.makedirs(os.path.dirname(image_save_path), exist_ok=True)
            image_data.save(image_save_path)
                
        print("All annotated images have been saved.")

    def upload_dataset(self, repo_name, private=True):
        data = []
        for subfolder in ['annotated_images', 'raw_images']:
            image_dir = os.path.join(self.base_image_dir, subfolder)
            for root, _, files in os.walk(image_dir):
                for filename in files:
                    if filename.endswith('.jpg'):
                        image_path = os.path.join(root, filename)
                        data.append({'path': image_path, 'image': image_path})
                        # print(f"Found image: {image_path}")  # Debugging line
                        
        if len(data) == 0:
            print("Error: No image files found.")
            return
        features = Features({
            'path': Value('string'),
            'image': Image()
        })
        
        dataset_dict = DatasetDict({
                            'train': Dataset.from_pandas(pd.DataFrame(data), features=features)
                        })
        try:
            repo_url = self.api.create_repo(repo_name, repo_type='dataset', private=private)
            repo = Repository(repo_name, clone_from=repo_url, repo_type='dataset')
        except Exception as e:
            print(f"Error: {e}")
        dataset_dict['train'].push_to_hub(repo_name, token=self.token)


# 用法示例
# token = "hf_xxxxxxxxxxxxxxxxxxxxxxxx"
# split = 'train'
# data_dir = 'default'
# name = 'train_dataset_20240119_images'
# user = "raidavid"
# manager = DatasetManager(token, base_image_dir=f'./saved_images_{name}_{split}/')
# manager.download_dataset(f"{user}/{name}", data_dir=data_dir, split=split)
# manager.upload_dataset("raidavid/Project_Images_train", private=False)
