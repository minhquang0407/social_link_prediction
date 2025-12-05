from collections import defaultdict
import torch
import torch.nn.functional as F
from torch_geometric.data import HeteroData
from torch_geometric.loader import LinkNeighborLoader
from torch_geometric.nn import SAGEConv, to_hetero
from sentence_transformers import SentenceTransformer
import networkx as nx
import pickle
import os
from tqdm import tqdm

from demo import edge_label
from pathlib import Path

    CURRENT_SCRIPT_DIR = Path(__file__).resolve().parent
    PROJECT_DIR = CURRENT_SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / 'models' / 'data_prepare'
MODEL_DIR = PROJECT_DIR / 'models'
PATHS = {
    'data': str(DATA_DIR/'processed_data.pt'),
    'mapping': str(DATA_DIR/'mappings.pkl'),
    'model': str(MODEL_DIR/'gnn_model.pth')
}

class GNN(torch.nn.Module):
    def __init__(self,hidden_channels, out_channels):
        super().__init__()
        self.conv1 = SAGEConv((-1,-1),hidden_channels)
        self.bn1 = torch.nn.BatchNorm1d(hidden_channels)
        self.conv2 = SAGEConv((-1,-1),out_channels)
    def forward(self,x,edge_index):
        x = self.conv1(x,edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.conv2(x,edge_index)
        return x

class AIModel:
    def __init__(self, G_full):
        self.G_full = G_full
        self.model = None
        self.data = None
        self.node_mapping = {}
        self.rev_node_mapping = {}
        self.text_encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    def _get_node_matrix_feature(self, node_list, ntype):
        feature_matrix = []
        years = []
        for node_id in node_list:
            node_data = self.G_full.nodes[node_id]
            name = node_data.get('name', 'Unknown')
            desc = node_data.get('description', '')
            interests = node_data.get('interests', '')
            birthplace = node_data.get('birthPlace', '')
            country = node_data.get('country', '')
            full_text = (f"Name: {name}. Description: {desc}. "
                         f"Interests: {interests}. "
                         f"Birthplace: {birthplace}. Country: {country}.")
            feature_matrix.append(full_text)
            if ntype == 'person':
                raw_year = node_data.get('birthYear')
                MIN_YEAR , MAX_YEAR =  1900,2025
                year = max(MIN_YEAR, min(raw_year, MAX_YEAR))
                norm_year = (year - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)
                years.append(norm_year)
        embeddings = self.text_encoder.encode(feature_matrix)
        text_tensor = torch.tensor(embeddings,dtype=torch.float)

        if ntype == 'person':
            year_tensor = torch.tensor(years, dtype=torch.float).view(-1, 1)
            return torch.cat([text_tensor, year_tensor], dim=1)
        else:
            return text_tensor
    def prepare_data(self,force_process=False):
        print("Preparing HeteroData...")
        if not force_process and os.path.exists(PATHS['data']) and os.path.exists(PATHS['mapping']):
            print("🔄 Đang load dữ liệu đã xử lý từ đĩa...")
            self.data = torch.load(PATHS['data'])
            with open(PATHS['mapping'], 'rb') as f:
                self.node_mapping, self.rev_mapping = pickle.load(f)
            print("✅ Load dữ liệu thành công!")
            return

        print("⚠️ Không tìm thấy file processed. Bắt đầu xử lý từ NetworkX...")

        self.data = HeteroData()
        #Group nodes by type
        node_by_type = defaultdict(list)
        for node_id, node_data in self.G_full.nodes(data=True):
            ntype = node_data.get('type', 'unknown')
            node_by_type[ntype].append(node_id)

        #Create feature matrix by type
        for ntype, node_list in node_by_type.items():
            self.node_mapping[ntype] = {nid:i for i,nid in enumerate(node_list)}
            self.rev_node_mapping[ntype] = {i:nid for i,nid in enumerate(node_list)}
            self.data[ntype].x = self._get_node_matrix_feature(node_list, ntype)
            self.data[ntype].num_nodes = len(node_list)

        #Processing edges
        edges_dict = defaultdict(lambda: [[], []])
        knows_src = []
        knows_dst = []
        for u, v, attr in tqdm(self.G_full.edges(data=True)):
            src_type = self.G_full.nodes[u].get('type')
            dst_type = self.G_full.nodes[v].get('type')

            if not src_type or not dst_type: continue

            rel_label = attr.get('label', 'related_to')

            try:
                u_idx = self.node_mapping[src_type][u]
                v_idx = self.node_mapping[dst_type][v]
            except KeyError: continue

            edge_key = (src_type, rel_label, dst_type)
            edges_dict[edge_key][0].append(u_idx)
            edges_dict[edge_key][1].append(v_idx)

            if src_type == 'person' and dst_type == 'person':
                knows_src.append(u_idx)
                knows_dst.append(v_idx)
        # HeteroData
        for (src_t, rel, dst_t), (src_list, dst_list) in edges_dict.items():
            edge_index = torch.tensor([src_list, dst_list], dtype=torch.long)
            self.data[src_t, rel, dst_t].edge_index = edge_index

            self.data[dst_t, f"rev_{rel}" , src_t].edge_index = edge_index.flip(0)

        if knows_src:
            #Phải tạo 2 cạnh thuận và nghịch để GNN hoạt động tốt
            #Nhưng knows là quan hệ 2 chiều nên phải nối dài danh sách thay vì tạo 1 cái mới
            edge_index_forward = torch.tensor([knows_src, knows_dst], dtype=torch.long)
            edge_index_backward = edge_index_forward.flip(0)

            final_edge_index = torch.cat([edge_index_forward, edge_index_backward], dim=1)
            self.data['person', 'knows', 'person'].edge_index = final_edge_index

        print("✅ Data Prepared!")
        print("💾 Đang lưu xuống đĩa...")
        torch.save(self.data, PATHS['data'])
        with open(PATHS['mapping'], 'wb') as f:
            pickle.dump((self.node_mapping, self.rev_mapping), f)
        print("✅ Xử lý xong!")

    def train(self, epochs = 20, batch_size = 128, save_path='model.pth'):

        if self.data is None:
            self.prepare_data()

        base_model = GNN(hidden_channels=64, out_channels=32)
        self.model = to_hetero(base_model, self.data.metadata(), aggr='sum').to(self.device)

        self.data.to(self.device)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.01)

        #LOADER

        target_edge_type = ('person','spouse','person')
        if target_edge_type not in self.data.edge_index_dict:
            print(f"CRITICAL ERROR: Không tìm thấy cạnh {target_edge_type}")
            return
        loader = LinkNeighborLoader(
            self.data,
            num_neighbors=[10,5],
            edge_label_index = (target_edge_type,self.data[target_edge_type].edge_index),
            neg_sampling_ratio= 1.0,
            batch_size=batch_size,
            shuffle=True,
        )
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch in tqdm(loader, desc=f"Epoch {epoch + 1}"):
                batch = batch.to(self.device)
                optimizer.zero_grad()

                z_dict = self.model(batch.x_dict, batch.edge_index_dict)

                # Lấy nhãn và index
                edge_label_index = batch[target_edge_type].edge_label_index
                edge_label = batch[target_edge_type].edge_label

                z_src = z_dict['person'][edge_label_index[0]]
                z_dst = z_dict['person'][edge_label_index[1]]

                scores = (z_src * z_dst).sum(dim=-1)
                loss = F.binary_cross_entropy_with_logits(scores, edge_label)

                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            print(f"Epoch {epoch + 1} Loss: {total_loss:.4f}")
        print("💾 Lưu model...")
        torch.save(self.model.state_dict(), PATHS['model'])

    def load_model(self):
        if not os.path.exists(input_path):
            print("Model file not found!")
            return
        print(f"Loading model from {input_path}...")
        if self.data is None:
            self.prepare_data()
        base_model = GNN(hidden_channels=64, out_channels=32)
        self.model = to_hetero(base_model, self.data.metadata(), aggr='sum')
        self.model.load_state_dict(torch.load(PATHS['model'], map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        print("Model loaded successfully!")

    def predict_top_partners(self, person_id, top_k = 5, batch_size = 128):
        if self.model is None: self.load_model()
        self.model.eval()

        try:
            p_idx = self.node_mapping['person'][person_id]
        except KeyError:
            return "Người này không tồn tại"

        loader = LinkNeighborLoader(
            self.data,
            num_neighbors=[10, 5],
            input_nodes=('person', None),
            batch_size=batch_size,
            shuffle=False
        )

        all_embeddings = []

        with torch.no_grad():
            for batch in tqdm(loader, desc="Computing Embeddings"):
                batch = batch.to(self.device)
                z_dict = self.model(batch.x_dict, batch.edge_index_dict)
                batch_person_z = z_dict['person'][:batch.batch_size]
                all_embeddings.append(batch_person_z.cpu())

        z_all_person = torch.cat(all_embeddings, dim=0)


        z_A = z_all_person[p_idx]

        scores = torch.matmul(z_all_person, z_A)

        top_scores, top_indices = torch.topk(scores, k=top_k + 1)

        results = []

        for score, index in zip(top_scores, top_indices):
            index = index.item()
            if index == p_idx: continue

            real_id = self.rev_node_mapping['person'][index]
            name = self.G_full[real_id]['name']
            results.append((name, score.item()))

        return results[:top_k]




