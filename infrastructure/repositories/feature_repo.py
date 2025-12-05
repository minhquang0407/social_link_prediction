import torch
import pickle
import os
import sys
from pathlib import Path
FILE_PATH = Path(__file__).resolve()
PROJECT_DIR = FILE_PATH.parent.parent.parent
sys.path.append(str(PROJECT_DIR))
from core.interfaces import ITrainingDataRepository


class PyGDataRepository(ITrainingDataRepository):
    def __init__(self, data_path, mapping_path):
        # Nhận đường dẫn từ Settings
        self.data_path = data_path
        self.mapping_path = mapping_path

    def save_data(self, data, mapping):
        try:
            # Đảm bảo thư mục cha tồn tại
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

            print(f"REPO: Đang lưu Processed Data vào {self.data_path}...")
            torch.save(data, self.data_path)

            print(f"REPO: Đang lưu Mapping vào {self.mapping_path}...")
            with open(self.mapping_path, 'wb') as f:
                pickle.dump(mapping, f)
            return True
        except Exception as e:
            print(f"REPO ERROR: {e}")
            return False

    def load_data(self):
        if not os.path.exists(self.data_path) or not os.path.exists(self.mapping_path):
            return None, None

        try:
            print("REPO: Đang tải Processed Data...")
            # map_location='cpu' để an toàn khi load trên máy không có GPU
            data = torch.load(self.data_path, map_location='cpu')

            with open(self.mapping_path, 'rb') as f:
                mapping = pickle.load(f)

            return data, mapping
        except Exception as e:
            print(f"REPO ERROR: {e}")
            return None, None