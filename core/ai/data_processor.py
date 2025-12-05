import torch
import numpy as np
from torch_geometric.data import HeteroData
from collections import defaultdict
from sentence_transformers import SentenceTransformer
import networkx as nx
from tqdm import tqdm


class GraphDataProcessor:
    """
    1. Tạo vector đặc trưng từ thuộc tính node.
    2. Chuyển đổi đồ thị NetworkX sang PyG HeteroData.
    """

    def __init__(self):
        print("CORE: Đang tải model Sentence-BERT...")
        self.text_encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    def _create_node_features(self, G, node_list, ntype):
        """
        (Hàm nội bộ) Tạo ma trận đặc trưng cho một danh sách node cùng loại.
        """
        feature_text_list = []
        years = []

        # Cấu hình chuẩn hóa năm sinh
        MIN_YEAR, MAX_YEAR = 1900, 2025

        for node_id in node_list:
            node_data = G.nodes[node_id]

            # 1. Xử lý Text (Tên, Mô tả, Sở thích...)
            name = node_data.get('name', 'Unknown')
            desc = node_data.get('description', '')
            interests = node_data.get('interests', '')
            birthplace = node_data.get('birthPlace', '')
            country = node_data.get('country', '')

            full_text = (f"Name: {name}. Description: {desc}. "
                         f"Interests: {interests}. "
                         f"Birthplace: {birthplace}. Country: {country}.")
            feature_text_list.append(full_text)

            # 2. Xử lý Số (Năm sinh) - Chỉ cho 'person'
            if ntype == 'person':
                raw_year = node_data.get('birthYear', 1980)
                try:
                    raw_year = float(raw_year)
                except:
                    raw_year = 1980

                # Kẹp giá trị và chuẩn hóa về [0, 1]
                year = max(MIN_YEAR, min(raw_year, MAX_YEAR))
                norm_year = (year - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)
                years.append(norm_year)

        # Encode Text batch (nhanh hơn loop từng cái)
        embeddings = self.text_encoder.encode(feature_text_list)
        text_tensor = torch.tensor(embeddings, dtype=torch.float)

        # Gộp với Year (nếu là person)
        if ntype == 'person':
            year_tensor = torch.tensor(years, dtype=torch.float).view(-1, 1)
            return torch.cat([text_tensor, year_tensor], dim=1)
        else:
            return text_tensor

    def process_graph_to_pyg(self, G):
        """
        Input: NetworkX Graph
        Output: (HeteroData, node_mapping, rev_node_mapping)
        """
        print("CORE: Bắt đầu chuyển đổi đồ thị sang HeteroData...")
        data = HeteroData()

        # 1. Xử lý Nodes & Features
        # Gom node theo loại (person, school, movie...)
        node_by_type = defaultdict(list)
        for node_id, node_data in G.nodes(data=True):
            ntype = node_data.get('type', 'unknown')
            node_by_type[ntype].append(node_id)

        node_mapping = {}  # String ID -> Int Index
        rev_node_mapping = {}  # Int Index -> String ID

        for ntype, node_list in node_by_type.items():
            # Tạo mapping
            node_mapping[ntype] = {nid: i for i, nid in enumerate(node_list)}
            rev_node_mapping[ntype] = {i: nid for i, nid in enumerate(node_list)}

            # Tạo feature matrix (Gọi hàm nội bộ _create_node_features)
            print(f"   -> Đang tạo đặc trưng cho loại '{ntype}' ({len(node_list)} nodes)...")
            data[ntype].x = self._create_node_features(G, node_list, ntype)
            data[ntype].num_nodes = len(node_list)

        # 2. Xử lý Edges

        edges_dict = defaultdict(lambda: [[], []])
        knows_src = []
        knows_dst = []
        for u, v, attr in tqdm(G.edges(data=True)):
            src_type = G.nodes[u].get('type')
            dst_type = G.nodes[v].get('type')

            if not src_type or not dst_type: continue

            rel_label = attr.get('label', 'related_to')

            try:
                u_idx = node_mapping[src_type][u]
                v_idx = node_mapping[dst_type][v]
            except KeyError:
                continue

            edge_key = (src_type, rel_label, dst_type)
            edges_dict[edge_key][0].append(u_idx)
            edges_dict[edge_key][1].append(v_idx)

            if src_type == 'person' and dst_type == 'person':
                knows_src.append(u_idx)
                knows_dst.append(v_idx)
        # HeteroData
        for (src_t, rel, dst_t), (src_list, dst_list) in edges_dict.items():
            edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)
            data[src_t, rel, dst_t].edge_index = edge_index

            data[dst_t, f"rev_{rel}", src_t].edge_index = edge_index.flip(0)

        if knows_src:
            # Phải tạo 2 cạnh thuận và nghịch để GNN hoạt động tốt
            # Nhưng knows là quan hệ 2 chiều nên phải nối dài danh sách thay vì tạo 1 cái mới
            edge_index_forward = torch.tensor([knows_src, knows_dst], dtype=torch.long)
            edge_index_backward = edge_index_forward.flip(0)

            final_edge_index = torch.cat([edge_index_forward, edge_index_backward], dim=1)
            data['person', 'knows', 'person'].edge_index = final_edge_index


        print("CORE: Chuyển đổi hoàn tất.")
        return data, (node_mapping, rev_node_mapping)