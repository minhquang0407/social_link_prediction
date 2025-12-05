import networkx as nx
from core.interfaces import IPathFinder


class NetworkXBFSFinder(IPathFinder):
    """
    Triển khai thuật toán tìm kiếm đường đi ngắn nhất (BFS)
    sử dụng thư viện NetworkX.
    """

    def find_path(self, graph, start_id, end_id):
        try:
            path_ids = nx.shortest_path(graph, source=start_id, target=end_id)

            path_names = [graph.nodes[n].get('name', str(n)) for n in path_ids]

            return path_ids, path_names

        except nx.NetworkXNoPath:
            return [], []

        except Exception as e:
            print(f"Lỗi thuật toán BFS: {e}")
            return [], []

