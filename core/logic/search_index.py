
import sys
from pathlib import Path
FILE_PATH = Path(__file__).resolve()
PROJECT_DIR = FILE_PATH.parent.parent.parent
sys.path.append(str(PROJECT_DIR))
from core.interfaces import IGraphRepository

from collections import defaultdict


def build_search_index(G):
    """
    Hàm độc lập tạo chỉ mục tìm kiếm từ đồ thị G.
    Dựa trên thuộc tính 'normalized_name' đã được tính trước.
    """
    print("LOG: Đang xây dựng chỉ mục tìm kiếm (Tối ưu)...")
    search_map = defaultdict(list)

    # Lặp qua các node
    for node_id, data in G.nodes(data=True):
        # 1. Lấy key chuẩn hóa (đã tính sẵn ở Transformer)
        clean_key = data.get('normalized_name')

        # 2. Lấy tên gốc
        original_name = str(data.get('name', 'Unknown'))

        if clean_key and original_name:
            node_info = {
                "id": node_id,
                "name": original_name,
                "description": str(data.get('description', ''))
            }

            # 3. Thêm vào map
            search_map[clean_key].append(node_info)

    # Trả về cả Map và List các Keys (để RapidFuzz dùng)
    return search_map, list(search_map.keys())