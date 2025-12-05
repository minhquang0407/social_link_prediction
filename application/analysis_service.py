from core.algorithms.bfs import NetworkXBFSFinder
from core.interfaces import ISearchEngine


class AnalysisService:
    def __init__(self, graph, search_engine: ISearchEngine):
        """
        Service quản lý việc Phân tích.
        - graph: Đồ thị NetworkX.
        - search_engine: Đối tượng thực thi việc tìm kiếm (đã được khởi tạo và build index).
        """
        self.graph = graph
        self.path_finder = NetworkXBFSFinder()

        # Dependency Injection: Nhận bộ máy tìm kiếm từ bên ngoài
        self.search_engine = search_engine

    def search_person(self, query_name, threshold=60.0):
        """
        Tìm kiếm mờ (Delegate cho search_engine).
        """
        # Gọi hàm search_best từ file fuzzy_search.py thông qua Interface
        return self.search_engine.search_best(query_name, threshold)

    def find_connection(self, id_a, id_b):
        """
        Tìm đường đi giữa 2 người.
        """
        # 1. Kiểm tra dữ liệu đầu vào
        str_id_a = str(id_a)
        str_id_b = str(id_b)

        if str_id_a == str_id_b:
            return {"success": False, "message": "Bạn đã nhập cùng một người."}

        # 2. Kiểm tra tồn tại trong đồ thị
        if self.graph is None:
            return {"success": False, "message": "Chưa có dữ liệu đồ thị."}

        if id_a not in self.graph:
            return {"success": False, "message": f"ID '{id_a}' không tồn tại."}
        if id_b not in self.graph:
            return {"success": False, "message": f"ID '{id_b}' không tồn tại."}

        # 3. Gọi thuật toán BFS
        ids, names = self.path_finder.find_path(self.graph, id_a, id_b)

        if ids:
            return {
                "success": True,
                "path_ids": ids,
                "path_names": names
            }

        # 4. Xử lý trường hợp không có đường đi
        name_a = self.graph.nodes[id_a].get('name', id_a)
        name_b = self.graph.nodes[id_b].get('name', id_b)
        return {
            "success": False,
            "message": f"Không tìm thấy liên kết giữa **{name_a}** và **{name_b}**."
        }