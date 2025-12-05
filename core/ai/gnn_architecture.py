import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, to_hetero


class GraphSAGE(torch.nn.Module):
    def __init__(self,hidden_channels, out_channels):
        super().__init__()
        self.conv1 = SAGEConv((-1,-1),hidden_channels)
        self.bn1 = torch.nn.BatchNorm1d(hidden_channels)
        self.conv2 = SAGEConv((-1,-1),out_channels)
    def forward(self,x,edge_index):
        x = self.conv1(x,edge_index)
        #x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.conv2(x,edge_index)
        return x

    def decode(self, z_dict, edge_label_index, edge_type):
        """
        Tính điểm liên kết (Dot product) dựa trên vector embeddings (Z).
        """
        src_type, _, dst_type = edge_type

        # Lấy vector Z của node nguồn và node đích
        z_src = z_dict[src_type][edge_label_index[0]]
        z_dst = z_dict[dst_type][edge_label_index[1]]

        # Dot product (nhân tích vô hướng)
        return (z_src * z_dst).sum(dim=-1)
