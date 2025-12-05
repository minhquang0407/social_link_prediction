import streamlit as st
import sys
import subprocess
from pathlib import Path

from config.settings import GRAPH_PATH, MODEL_PATH, PYG_DATA_PATH, MAPPING_PATH
from infrastructure.repositories import PickleGraphRepository, ModelRepository, PyGDataRepository
from application import AIService, AnalysisService
from presentation import AppRunner
from core.logic import build_search_index
from core.logic import RapidFuzzySearch
from core.algorithms import NetworkXBFSFinder
# --- 1. HÀM LOAD TÀI NGUYÊN VÀ LẮP RÁP SERVICE (BOOTSTRAP) ---

@st.cache_resource(show_spinner="Đang khởi động hệ thống...")
def bootstrap_services():
    """
    Hàm này chạy 1 lần duy nhất để lắp ráp và cache các Services đã nạp dữ liệu.
    """
    print("LOG: Bắt đầu quá trình Bootstrap hệ thống...")

    # --- INFRASTRUCTURE (Tầng 1) ---
    graph_repo = PickleGraphRepository(GRAPH_PATH)
    model_repo = ModelRepository(MODEL_PATH)
    feature_repo = PyGDataRepository(PYG_DATA_PATH,MAPPING_PATH)

    # 1. Load Graph
    G_full = graph_repo.load_graph()
    if G_full is None:
        print("LỖI: Không tải được đồ thị G_full.gpickle.")
        return None, None

    # 2. Lấy Search Index
    search_index = build_search_index(G_full)

    # 3. Load Model AI
    ai_model = model_repo.load_model()
    hetero_data, mapping = feature_repo.load_data()
    # --- APPLICATION (Tầng 2: Lắp ráp các Service) ---

    search_engine = RapidFuzzySearch(search_index)

    # Lắp ráp các Service)
    analysis_service = AnalysisService(G_full,search_engine)
    ai_service = AIService(G_full, ai_model, hetero_data, mapping)
    # Lắp ráp AI Service


    print("LOG: Hệ thống Services đã được lắp ráp thành công.")
    return analysis_service, ai_service


def run_web_app():
    """Lắp ráp Services và khởi chạy giao diện AppRunner."""
    analysis_service, ai_service = bootstrap_services()

    if analysis_service and ai_service:
        from presentation import AppRunner
        app = AppRunner(analysis_service, ai_service)
        app.run()
    else:
        st.set_page_config(layout="wide", page_title="Social Network Analysis")
        st.title("⚠️ Lỗi Hệ thống")
        st.error("Không thể khởi động ứng dụng. Vui lòng kiểm tra file dữ liệu `G_full.gpickle` và chạy lại.")


# --- 3. HÀM CHẠY CÁC LỆNH TIỆN ÍCH (CLI) ---

def run_cli_command(command):
    """
    Xử lý các lệnh CLI: etl, train.
    Đây là nơi gọi các scripts/run_etl.py (dùng subprocess)
    """
    if command == "etl":
        print("BẮT ĐẦU: Chạy quy trình thu thập và xử lý dữ liệu (ETL)...")
        subprocess.run(["python", "scripts/etl_run.py"], check=True)
    elif command == "train":
        print("BẮT ĐẦU: Chạy quy trình huấn luyện AI...")
        subprocess.run(["python", "scripts/train_model.py"], check=True)
    else:
        print("\nSử dụng: python main.py [COMMAND]")
        print("COMMANDS:")
        print("  --etl     : Chạy quy trình thu thập và xử lý dữ liệu.")
        print("  --train   : Huấn luyện mô hình GNN (Sử dụng dữ liệu G_full đã có).")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith('--'):
        command = sys.argv[1].lstrip('--')
        run_cli_command(command)
    else:
        # Nếu không có tham số CLI, chạy Web App
        run_web_app()