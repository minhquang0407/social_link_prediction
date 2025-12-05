import sys
import json
import networkx as nx
import pandas as pd
import os
from unidecode import unidecode
from collections import defaultdict
from pathlib import Path

FILE_PATH = Path(__file__).resolve()
PROJECT_DIR = FILE_PATH.parent.parent.parent
sys.path.append(str(PROJECT_DIR))

class GraphTransformer:
    def __init__(self):
        # Khởi tạo một đồ thị rỗng
        self.G = nx.Graph()
        self.person_interests_map = defaultdict(set)
        print("GraphTransformer initialized.")

    def _load_and_flatten_json(self, raw_filepath):
        if not os.path.exists(raw_filepath):
            print(f"Cảnh báo: Không tìm thấy file {raw_filepath}")
            return pd.DataFrame()

        try:
            with open(raw_filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            df = pd.json_normalize(data['results']['bindings'])
            new_columns = {col: col.replace('.value', '') for col in df.columns}
            df = df.rename(columns=new_columns)
            return df
        except Exception as e:
            print(f"❌ Lỗi khi đọc file {raw_filepath}: {e}")
            return pd.DataFrame()

    def _clean_data(self, data, label_col):
        if data.empty or label_col not in data.columns:
            return data
        qid_pattern = r'^Q\d+$'
        data_clean = data[~data[label_col].str.match(qid_pattern, na=False)]
        return data_clean

    def _add_generic_relation(self, df, target_node_type, rel_label):
        attribute_map = {
            "personDescription": "description",
            "birthYear": "birth_year",
            "birthPlaceLabel": "place_of_birth",
            "countryLabel": "country"
        }

        df = self._clean_dataframe(df, 'personLabel')
        df = self._clean_dataframe(df, 'objectLabel')

        for _, row in df.iterrows():
            try:
                p_id = row['person'].split('/')[-1]
                obj_id = row['object'].split('/')[-1]
            except (KeyError, AttributeError):
                continue

            p_name = row.get('personLabel', 'Unknown')
            obj_name = row.get('objectLabel', 'Unknown')

            try:
                p_norm = unidecode(p_name).lower()
            except:
                p_norm = ""

            person_attrs = {
                "name": p_name,
                "normalized_name": p_norm,
                "type": "person"
            }
            for col, attr_key in attribute_map.items():
                if col in row and pd.notna(row[col]):
                    person_attrs[attr_key] = str(row[col])

            if p_id in self.person_interests_map:
                person_attrs["interests"] = ",".join(self.person_interests_map[p_id])

            self.G.add_node(p_id, **person_attrs)

            obj_norm = unidecode(obj_name).lower() if obj_name else ""
            self.G.add_node(
                obj_id,
                name=obj_name,
                normalized_name=obj_norm,
                type=target_node_type
            )

            # --- EDGE ---
            label = row.get('relationshipLabel', rel_label)
            self.G.add_edge(p_id, obj_id, label=label)

    def _aggregate_interests(self, file_list):
        print("Đang tổng hợp sở thích...")
        for filepath, interest_key in file_list:
            interest_data = self._load_and_flatten_json(filepath)

            if interest_data.empty: continue

            # Tìm tên cột nhãn động (ví dụ: sportLabel)
            label_col = f"{interest_key}Label"  # Đã bỏ .value ở bước load

            # Fallback nếu không tìm thấy cột cụ thể
            if label_col not in df.columns:
                label_col = 'objectLabel'

            if 'person' not in df.columns or label_col not in df.columns: continue

            # Lọc rác
            df = self._clean_data(df, label_col)

            for _, row in df.iterrows():
                try:
                    pid = row['person'].split('/')[-1]
                    val = row[label_col]
                    if val: self.person_interests_map[pid].add(val)
                except:
                    continue


    def build_full_graph(self,files_config ,interest_configs=None):
            if interest_files:
                self._aggregate_interests(interest_files)
            for file_path, target_type, label in files_config:
                df = self._load_and_flatten_json(file_path)
                if not df.empty:
                    self._add_generic_relation(df, target_type, label)

            return self.G






