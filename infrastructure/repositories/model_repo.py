import torch
import os
import pickle
import sys
from pathlib import Path
FILE_PATH = Path(__file__).resolve()
PROJECT_DIR = FILE_PATH.parent.parent.parent
sys.path.append(str(PROJECT_DIR))
from core.interfaces import IModelRepository


class ModelRepository(IModelRepository):
    """
    Kho chứa Model AI. Hỗ trợ cả PyTorch (.pth) và Pickle (.pkl).
    """

    def __init__(self, file_path: Path):
        self.file_path = str(file_path)

    def save_model(self, model):
        """
        Lưu model xuống đĩa.
        """
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        try:
            print(f"REPO: Đang lưu model vào {self.file_path}...")

            if isinstance(model, torch.nn.Module):
                torch.save(model.state_dict(), self.file_path)
            else:
                with open(self.file_path, "wb") as f:
                    pickle.dump(model, f)

            print("REPO: Lưu model thành công!")
            return True
        except Exception as e:
            print(f"REPO ERROR: Không thể lưu model. Lỗi: {e}")
            return False

    def load_model(self, model=None, device=None):
        """
        Tải model từ đĩa.
        - model_architecture: (Bắt buộc cho PyTorch) Là object model rỗng để nạp trọng số vào.
        - device: 'cpu' hoặc 'cuda'.
        """
        if not os.path.exists(self.file_path):
            print(f"REPO WARNING: Không tìm thấy file model: {self.file_path}")
            return None

        try:
            if model is not None:
                if device is None:
                    device = torch.device('cpu')

                state_dict = torch.load(self.file_path, map_location=device)
                model.load_state_dict(state_dict)
                print("REPO: Đã nạp trọng số vào PyTorch model.")
                return model

            with open(self.file_path, "rb") as f:
                model = pickle.load(f)
                print("REPO: Đã tải model Pickle.")
                return model

        except Exception as e:
            print(f"REPO ERROR: Lỗi khi tải model: {e}")
            return None