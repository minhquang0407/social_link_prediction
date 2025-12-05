import sys
import os
from pathlib import Path
import itertools  # Dùng cho Grid Search

# --- CẤU HÌNH ĐƯỜNG DẪN ---
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
import torch.nn.functional as F
from torch_geometric.loader import LinkNeighborLoader
from torch_geometric.nn import to_hetero
from torch_geometric.transforms import RandomLinkSplit
from sklearn.metrics import roc_auc_score
from tqdm import tqdm
import pickle
import argparse
import numpy as np

from config.settings import (
    GRAPH_PATH, MODEL_PATH, PYG_DATA_PATH, MAPPING_PATH,
    INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM, EPOCHS, BATCH_SIZE, LEARNING_RATE
)
from infrastructure.repositories.graph_repo import PickleGraphRepository
from core.ai.gnn_architecture import GraphSAGE
from core.ai.data_processor import GraphDataProcessor
from infrastructure.repositories.feature_repo import PyGDataRepository


# --- 1. CHUẨN BỊ DỮ LIỆU ---
def get_or_prepare_data():
    """Tải hoặc tạo mới dữ liệu PyG."""
    feature_repo = PyGDataRepository(PYG_DATA_PATH, MAPPING_PATH)
    data, mapping = feature_repo.load_data()

    if data is None:
        print("⚠️ Chưa có dữ liệu PyG. Đang xử lý từ NetworkX...")
        repo = PickleGraphRepository(GRAPH_PATH)
        G = repo.load_graph()
        if G is None:
            raise FileNotFoundError(f"Không tìm thấy đồ thị tại {GRAPH_PATH}")

        processor = GraphDataProcessor()
        data, mapping = processor.process_graph_to_pyg(G)
        feature_repo.save_data(data, mapping)

    return data



# --- 2. CÁC HÀM HUẤN LUYỆN & ĐÁNH GIÁ ---

def train_epoch(model, loader, optimizer, device, target_edge_type):
    """Chạy 1 epoch huấn luyện."""
    model.train()
    total_loss = 0
    total_examples = 0

    for batch in tqdm(loader, desc="Training", leave=False):
        batch = batch.to(device)
        optimizer.zero_grad()

        # Forward
        z_dict = model(batch.x_dict, batch.edge_index_dict)

        # Lấy nhãn và index cạnh cần dự đoán trong batch này
        edge_label_index = batch[target_edge_type].edge_label_index
        edge_label = batch[target_edge_type].edge_label

        # Decode (Tính điểm)
        src_type, _, dst_type = target_edge_type
        z_src = z_dict[src_type][edge_label_index[0]]
        z_dst = z_dict[dst_type][edge_label_index[1]]
        out = (z_src * z_dst).sum(dim=-1)

        # Loss
        loss = F.binary_cross_entropy_with_logits(out, edge_label)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * edge_label.size(0)
        total_examples += edge_label.size(0)

    return total_loss / total_examples


@torch.no_grad()
def evaluate(model, loader, device, target_edge_type):
    """Đánh giá mô hình (tính AUC)."""
    model.eval()
    preds = []
    ground_truths = []

    for batch in tqdm(loader, desc="Evaluating", leave=False):
        batch = batch.to(device)
        z_dict = model(batch.x_dict, batch.edge_index_dict)

        edge_label_index = batch[target_edge_type].edge_label_index
        edge_label = batch[target_edge_type].edge_label

        src_type, _, dst_type = target_edge_type
        z_src = z_dict[src_type][edge_label_index[0]]
        z_dst = z_dict[dst_type][edge_label_index[1]]

        out = (z_src * z_dst).sum(dim=-1).sigmoid()

        preds.append(out.cpu().numpy())
        ground_truths.append(edge_label.cpu().numpy())

    return roc_auc_score(np.concatenate(ground_truths), np.concatenate(preds))


# --- 3. CHIẾN LƯỢC CHẠY ---

def train_one_config(data, config, device, target_edge_type, final_mode=False):
    """
    Huấn luyện mô hình với 1 bộ tham số cụ thể.
    """
    # 1. KHỞI TẠO TỪ ĐIỂN LỊCH SỬ
    history = {
        "epoch": [],
        "loss": [],
        "val_auc": []  # Có thể rỗng nếu là final_mode
    }
    hidden_dim = config['hidden_dim']
    lr = config['lr']
    epochs = config['epochs']

    print(f"\n⚙️ Cấu hình: Hidden={hidden_dim}, LR={lr}")

    # 1. Chia dữ liệu (nếu không phải final)
    if final_mode:
        train_data = data
        val_loader = None
    else:
        # RandomLinkSplit để tạo tập Train/Val/Test
        transform = RandomLinkSplit(
            num_val=0.1,
            num_test=0.1,
            is_undirected=True,
            add_negative_train_samples=False,
            edge_types=[target_edge_type]
        )
        train_data, val_data, test_data = transform(data)

        # Loader cho tập Validation
        val_loader = LinkNeighborLoader(
            val_data,
            num_neighbors=[10, 5],
            edge_label_index=(target_edge_type, val_data[target_edge_type].edge_label_index),
            edge_label=val_data[target_edge_type].edge_label,
            batch_size=BATCH_SIZE,  # Dùng batch size lớn hơn cho eval cũng được
            shuffle=False
        )

    # 2. Loader cho tập Train
    # (Quan trọng: LinkNeighborLoader giúp không tràn RAM)
    train_loader = LinkNeighborLoader(
        train_data,
        num_neighbors=[10, 5],
        edge_label_index=(target_edge_type, train_data[target_edge_type].edge_index),
        neg_sampling_ratio=1.0,
        batch_size=BATCH_SIZE,
        shuffle=True
    )

    # 3. Model & Optimizer
    base_model = GraphSAGE(hidden_channels=hidden_dim, out_channels=OUTPUT_DIM, in_channels=INPUT_DIM)
    model = to_hetero(base_model, data.metadata(), aggr='sum').to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    best_val_auc = 0
    best_model_state = None

    # 4. Loop
    for epoch in range(1, epochs + 1):

        loss = train_epoch(model, train_loader, optimizer, device, target_edge_type)
        history["epoch"].append(epoch)
        history["loss"].append(float(loss))  # Ép kiểu float để tránh lỗi JSON
        log_msg = f"Epoch {epoch:03d} | Loss: {loss:.4f}"

        # Nếu có tập Val -> Đánh giá & Lưu Best Model
        if val_loader:
            val_auc = evaluate(model, val_loader, device, target_edge_type)
            history["val_auc"].append(float(val_auc))

            log_msg += f" | Val AUC: {val_auc:.4f}"

            if val_auc > best_val_auc:
                best_val_auc = val_auc
                best_model_state = model.state_dict()

        print(log_msg)
    if final_mode:
        print(f"💾 Đang lưu lịch sử huấn luyện vào {TRAINING_HISTORY_PATH}...")
        try:
            with open(TRAINING_HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
            print("✅ Đã lưu lịch sử thành công!")
        except Exception as e:
            print(f"❌ Lỗi khi lưu lịch sử: {e}")
    # Nếu Final Mode (không có Val), lấy state cuối cùng
    if final_mode:
        best_model_state = model.state_dict()
        best_val_auc = 1.0  # (Giả định)

    return best_val_auc, best_model_state


def run_grid_search():
    """Chạy tìm kiếm tham số tối ưu."""
    data = get_or_prepare_data()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    target_edge_type = ('person','knows','person')

    # Định nghĩa lưới tham số
    param_grid = {
        'hidden_dim': [64, 128],
        'lr': [0.01,0.001],
        'epochs': [20]  # Test nhanh 20 epoch
    }

    keys, values = zip(*param_grid.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

    best_auc = 0
    best_params = None

    print(f"🚀 Bắt đầu Grid Search trên {len(combinations)} cấu hình...")

    for config in combinations:
        auc, _ = train_one_config(data, config, device, target_edge_type)

        if auc > best_auc:
            best_auc = auc
            best_params = config
            print(f"🏆 Kỷ lục mới: AUC {auc:.4f} với {config}")

    print(f"\n✅ Grid Search Hoàn tất. Tốt nhất: {best_params} (AUC: {best_auc:.4f})")

    # Sau khi tìm được, chạy Final Training với tham số tốt nhất
    print("\n🏋️ Bắt đầu Final Training (100 Epochs) với tham số tốt nhất...")
    best_params['epochs'] = 100  # Train kỹ
    _, final_state = train_one_config(data, best_params, device, target_edge_type, final_mode=True)

    # Lưu Model cuối cùng
    print(f"💾 Đang lưu Final Model vào {MODEL_PATH}...")
    torch.save(final_state, MODEL_PATH)


if __name__ == "__main__":
    run_grid_search()