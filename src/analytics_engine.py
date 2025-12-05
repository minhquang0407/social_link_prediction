from collections import defaultdict
from unidecode import unidecode
from rapidfuzz import process, fuzz, utils
import networkx as nx



class AnalyticsEngine:
    def __init__(self, G_full):
        self.graph = G_full 
        self.graph_lcc = None 
        self.analytics_results = {} # (Lưu kết quả offline)
        self.search_index = self.build_search_index()

    def build_search_index(self):
        search_map = defaultdict(list)
        for node_id, data in self.graph.nodes(data=True):
            clean_key = data.get('normalized_name')
            original_name = str(data.get('name', 'Unknown'))
            if clean_key and original_name:
                node_info = {
                    "id": node_id,
                    "name": original_name,
                    "description": str(data.get('description', ''))
                }
                search_map[clean_key].append(node_info)

        return search_map
    def search_fuzzy(self,user_input, threshold=50):
        if not user_input:
            return None, 0.0

        try:
            clean_input = unidecode(str(user_input)).lower()
        except Exception:
            return None, 0.0

        all_keys = list(self.search_index.keys())

        result = process.extractOne(clean_input, all_keys, scorer=fuzz.token_set_ratio, processor=utils.default_process)
        if result:
            best_match_key, score, _ = result
            if score >= threshold:
                people_list = self.search_index[best_match_key]
                return people_list[0],score
        return None, 0.0
    def _get_person_id(self, name):
        if name is None:
            return None
        for node_id, data in self.graph.nodes(data = True):
            current_name = data.get('name','')
            if current_name.lower() == name.lower():
               return node_id
        return None	

    # --- Module 1 (BFS) ---
    def find_path(self, id_a, id_b):
        if id_a == id_b: return [], ["Bạn đã nhập cùng một người."]
        try:
          path_ids = nx.shortest_path(self.graph, source = id_a, target = id_b)
          path_names = [self.graph.nodes[n].get('name') for n in path_ids]
          return path_ids, path_names
        except nx.NetworkXNoPath:
          name_a = self.graph.nodes[id_a].get('name')
          name_b = self.graph.nodes[id_b].get('name')
          return [], [f"Không có đường đi giữa **{name_a}** và **{name_b}**."]
        except Exception as e:
            return [], [f"Lỗi hệ thống: {str(e)}"]

    def get_ego_graph(self,node_id):
        pass
    def semantic_search(self,query):
        pass
    # --- Module 4 (Ego) ---
    def get_ego_network(self, name_a):
        # Logic: Lấy ID, lấy neighbors, G.subgraph, trả về G_ego
        pass

    # --- Module 3 (Analytics Offline) ---
    def calculate_offline_stats(self):
        # (Hàm này chạy RẤT LÂU)
        # Logic: Tìm G_lcc. Tính Centrality, Community, Avg Path...
        # Lưu kết quả vào self.analytics_results (một dict)
        # (Hàm này sẽ được chạy 1 lần)
        pass

    # --- Module 2 (XAI) ---
    def get_feature_importances(self, model_features_file):
        # (Logic đọc file model_features.json)
        pass


