import torch
import pickle
from core.ai import Predictor


class AIService:
    def __init__(self, G_full, model, data, mapping):
        self.G_full = G_full
        self.model = model
        self.data = data
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.node_mapping, self.rev_node_mapping = mapping
        self.predictor = Predictor()

        print("AI: Đang tính toán sẵn các vector (Caching)...")
        self.all_person_vectors = self.predictor.compute_all_embeddings(
            self.model, self.data, self.device
        )
        print("AI: Sẵn sàng!")

    def predict_top_partners(self, person_id, top_k=5):
        """
        Dự đoán Top đối tác tiềm năng.
        """
        # 1. Lấy Index từ ID
        if person_id not in self.node_mapping['person']:
            return []
        p_idx = self.node_mapping['person'][person_id]

        # 2. Lấy Vector của người đó (từ Cache)
        z_A = self.all_person_vectors[p_idx]

        # 3. Gọi Predictor để tính toán Toán học
        top_scores, top_indices = self.predictor.predict_top_k_similar(
            z_A, self.all_person_vectors, top_k
        )

        # 4. Mapping ngược: Index -> Tên
        results = []
        for score, index in zip(top_scores, top_indices):
            idx = index.item()
            if idx == p_idx: continue

            real_id = self.rev_node_mapping['person'][idx]
            name = self.G_full.nodes[real_id].get('name', 'Unknown')

            results.append((name, score.item()))

        return results[:top_k]

    def predict_link_score(self, id_a, id_b):
        """Dự đoán điểm giữa 2 người cụ thể"""
        try:
            idx_a = self.node_mapping['person'][id_a]
            idx_b = self.node_mapping['person'][id_b]

            vec_a = self.all_person_vectors[idx_a]
            vec_b = self.all_person_vectors[idx_b]

            return self.predictor.predict_link_score(vec_a, vec_b)
        except KeyError:
            return 0.0