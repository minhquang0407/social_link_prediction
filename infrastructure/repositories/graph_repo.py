import pickle
import os
import sys
import networkx as nx
from pathlib import Path
FILE_PATH = Path(__file__).resolve()
PROJECT_DIR = FILE_PATH.parent.parent.parent
sys.path.append(str(PROJECT_DIR))
from core.interfaces import IGraphRepository


class PickleGraphRepository(IGraphRepository):
    """
    Kho chứa đồ thị sử dụng định dạng Pickle của Python.
    Chịu trách nhiệm Đọc và Ghi file .gpickle cho toàn bộ dự án.
    """

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def save_graph(self, G: nx.Graph):
        """
        Lưu đồ thị NetworkX xuống đĩa.
        Tự động tạo thư mục cha nếu chưa tồn tại.
        """

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        try:
            print(f"REPO: Đang lưu đồ thị vào {self.file_path}...")

            # 2. Mở file chế độ Write Binary (wb)
            with open(self.file_path, "wb") as f:
                pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

            print("REPO: Lưu thành công!")
            return True

        except Exception as e:
            print(f"REPO ERROR: Không thể lưu đồ thị. Lỗi: {e}")
            return False

    def load_graph(self) -> nx.Graph:
        """
        Tải đồ thị từ đĩa lên RAM.
        Trả về None nếu file không tồn tại hoặc lỗi.
        """
        # 1. Kiểm tra file có tồn tại không
        if not os.path.exists(self.file_path):
            print(f"REPO WARNING: File không tồn tại: {self.file_path}")
            return None

        try:
            print(f"REPO: Đang tải đồ thị từ {self.file_path}...")

            with open(self.file_path, "rb") as f:
                G = pickle.load(f)

            print(f"REPO: Tải thành công! (Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()})")
            return G

        except Exception as e:
            print(f"REPO ERROR: Lỗi khi đọc file đồ thị: {e}")
            return None