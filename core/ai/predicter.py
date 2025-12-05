import torch
from core.interfaces import ILinkPredictor
from torch_geometric.loader import NeighborLoader
from tqdm import tqdm

class Predictor(ILinkPredictor):

    def compute_all_embeddings(self, model, data, device, batch_size = 128):
        """
        Chạy model 1 lần để lấy vector của TẤT CẢ các node.
        Hàm này dùng để cache vector Z.
        """
        model.eval()

        loader = NeighborLoader(
            data,
            num_neighbors=[10, 5],
            input_nodes=('person', None),
            batch_size=batch_size,
            shuffle=False
        )

        all_embeddings = []

        with torch.no_grad():
            for batch in tqdm(loader, desc="Computing Embeddings"):
                batch = batch.to(device)
                z_dict = model(batch.x_dict, batch.edge_index_dict)
                batch_size_actual = batch['person'].batch_size
                z_person_batch = z_dict['person'][:batch_size_actual]
                all_embeddings.append(z_person_batch.cpu())

        z_all_person = torch.cat(all_embeddings, dim=0)

        return z_all_person

    def predict_top_k_similar(self, target_vec,all_vectors, top_k=5):
        if target_vec.device != all_vectors.device:
            target_vec = target_vec.to(all_vectors.device)
        scores = torch.matmul(all_vectors, target_vec)

        top_scores, top_indices = torch.topk(scores, k=top_k + 1)


        return top_scores, top_indices

    def predict_link_score(self, vec_a, vec_b) -> float:
        if not isinstance(vec_a, torch.Tensor): vec_a = torch.tensor(vec_a)
        if not isinstance(vec_b, torch.Tensor): vec_b = torch.tensor(vec_b)
        score = (vec_a * vec_b).sum().item()
        prob = torch.sigmoid(torch.tensor(score)).item()
        return prob