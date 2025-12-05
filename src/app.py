import pickle
import streamlit as st
import time
from pathlib import Path
# from analytics_engine import AnalyticsEngine
# from ai_model import AIModel
CURRENT_SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_SCRIPT_DIR.parent

GRAPH_DIR = PROJECT_DIR / 'data_output'/ 'G_full.gpickle'

custom_css = """
<style>
/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0004ffff; /* Màu nền sidebar */
    color: white; /* **Màu chữ trắng** cho sidebar */
}

/* body */
body {
    background-color: #f0f2f6;
    color: white;
}

.main-content {
    color: white;
}
</style>
"""
st.set_page_config(layout="wide", page_title="Social Network Analysis")
st.markdown(custom_css, unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "Trang chủ"
def get_readable_relationship(G, id_A, id_B, label):
    # ... (xử lý cha/con cũ) ...
    year_A = G.nodes[id_A].get('birth_year', 0)
    year_B = G.nodes[id_B].get('birth_year', 0)
    if label == "father":
        if year_A == 0 or year_B == 0:
            return "--[ father/son ]-->"

        elif year_A < year_B:  # A già hơn B
            return "--[ father of ]-->"
        else:
            return "--[ son of ]-->"
    elif label == "mother":
        if year_A == 0 or year_B == 0:
            return "--[ mother ]-->"
        elif year_A < year_B: return "--[ mother of ]-->"
        else:
            return "--[ son of ]-->"
    elif label == "mentor_student":
        if year_A == 0 or year_B == 0:
            return "--[ advisor/student ]-->"

        elif year_A < year_B:  # A già hơn B
            return "--[ advisor of ]-->"
        else:
            return "--[ student of ]-->"

    return f"--[ {label} ]-->"


def writer(text: str, speed: float = 0.03, key=None):
    if text not in st.session_state:
        placeholder = st.empty()
        displayed_text = ""
        for char in text:
            displayed_text += char
            placeholder.markdown(displayed_text + "▌")
            time.sleep(speed)
        placeholder.markdown(displayed_text)

        if text:
            st.session_state[text] = True
    else:
        st.markdown(text)
# #UI
# @st.cache_resource(show_spinner="Đang tải tài nguyên...")
# def load_resources():
#     if not GRAPH_DIR.exists(): return None
#     try:
#         with open(str(path), 'rb') as f:
#             G = pickle.load(f)
#             analytics_engine = AnalyticsEngine(G)
#             model = AIModel(G)
#             return G, analytics_engine, model
#     except Exception as e:
#         st.error(f"Lỗi file graph: {e}")
#         return None
#
#
#
# if 'resources_loaded' not in st.session_state:
#     with st.status("🚀 Đang khởi động hệ thống...", expanded=True) as status:
#         st.write("📂 Đang đọc dữ liệu đồ thị...")
#         social_graph, analytics_engine, model = load_resources()
#
#         if social_graph:
#             st.write("✅ Đã tải xong đồ thị.")
#             st.write("🧠 Đang khởi tạo bộ máy phân tích...")
#             st.session_state.social_graph = social_graph
#             st.session_state.analytics_engine = analytics_engine
#             st.session_state.model = model
#             st.session_state.resources_loaded = True
#             status.update(label="Hệ thống đã sẵn sàng!", state="complete", expanded=False)
#         else:
#             status.update(label="Không tìm thấy dữ liệu!", state="error")
#             st.stop()
# else:
#     social_graph = st.session_state.social_graph
#     analytics_engine = st.session_state.analytics_engine
#     model= st.session_state.model
def render_tab_bfs():
    writer("## Kiểm chứng Sáu Bậc Xa Cách", speed=0.02)
    with st.form("bfs_form"):
        col1, col2 = st.columns(2)
        with col1:
            name_a = st.text_input("Tên người 1", placeholder="Ví dụ: son tung")
        with col2:
            name_b = st.text_input("Tên người 2", placeholder="Ví dụ: obama")

        submitted = st.form_submit_button("🔍 Tìm đường đi")
    if submitted:
        if name_a and name_b:
            with st.status("Đang phân tích...", expanded=True) as status:
                #  p_a, s_a = analytics_engine.search_fuzzy(name_a)
                #  p_b, s_b = analytics_engine.search_fuzzy(name_b)
                # if not p_a or not p_b:
                #     status.update(label="Không tìm thấy người!", state="error")
                #     st.error("Vui lòng kiểm tra lại tên.")
                #     return
                #
                # st.markdown(f"""
                #     * **{name_a}** $\\rightarrow$ **{p_a['name']}** ({s_a:.0f}%)
                #     * **{name_b}** $\\rightarrow$ **{p_b['name']}** ({s_b:.0f}%)
                # """)
                with st.spinner("Đang tìm kiếm liên kết..."):
                    #path_ids, path_names = analytics_engine.find_path(p_a['id'],p_b['id'])
                    time.sleep(1)
                # if path_ids:
                #     st.success(f"Đã tìm thấy liên kết giữa **{p_a}** và **{p_b}**")
                # else:
                #     st.error(f"ERROR: {path_names}")
        else:
            st.warning("Vui lòng nhập đủ tên 2 người.")

def render_tab_ai():
    writer("# Dự đoán liên kết",speed=0.02 )

    writer("Dự đoán top k người sẽ có liên kết với A")

    name = st.text_input("Nhập tên muốn tìm:", placeholder="Ví dụ: Barack Obama")
    top = st.text_input("Nhập top:",placeholder="Ví dụ: 5")
    if st.button("🔍 Tìm kiếm"):
        with st.spinner("Đang tìm kiếm... Vui lòng chờ 3 giây"):
            pass
            # result = model.predict_top_partners(name, top)
        st.success("Hoàn tất!")
        # st.write(result)




def render_tab_analytics():
    writer("# Phân tích Toàn bộ Mạng lưới",speed=0.03)

    writer("Các chỉ số này được tính toán 'offline' trên toàn đồ thị",speed=0.01)

    if 'analytics_done' not in st.session_state:
        st.session_state.analytics_done = False

    if st.button("Chạy Phân tích"):
        with st.spinner("Đang chạy tính toán... Vui lòng chờ 3 giây"):
            time.sleep(3)
        st.success("Tính toán hoàn tất!")
        st.session_state.analytics_done = True
        if st.session_state.analytics_done:
            writer("### 📊 Thống kê Đường đi (Sáu Bậc Xa cách)", speed=0.03)
            col1, col2, col3 = st.columns(3)

            col1.metric(
                label="Số bậc Trung bình (AVG PATH)",
                value=2
            )

            col2.metric(
                label="Số bậc phổ biến (MODE PATH)",
                value=3
            )

            col3.metric(
                label="Đường kính (Diameter)",
                value=4
            )

            st.divider()
            time.sleep(0.5)

            writer("### 📊 Phân phối Bậc (Degree Distribution)", speed=0.03)
            # df_dist_degree = pd.DataFrame(
            #	analytics['degree_histogram'].items(),
            #	columns = ['Bậc', 'Số lượng']
            # ).set_index('Bậc')
            # st.bar_chart(df_dist_degree)
            time.sleep(0.5)

            writer("### 📊 Phân phối Đường đi (Path Length Distribution)",
                              speed=0.03)  # Vẽ biểu đồ 'path_length_histogram')
            st.divider()
            time.sleep(0.5)

            writer("### 👑 Phân tích 'Quyền lực' (Centrality Top 5)", speed=0.03)

            col_deg, col_bet, col_close, col_eig = st.columns(4)

            with col_deg:
                st.markdown("**1. Siêu Kết nối (Degree)**")

            with col_bet:
                st.markdown("**2. Môi giới (Betweenness)**")

            with col_close:
                st.markdown("**3. Trung tâm (Closeness)**")

            with col_eig:
                st.markdown("**4. Ảnh hưởng (Eigenvector)**")


def render_tab_ego():
    pass



# --- Phần Sidebar ---
with st.sidebar:
    st.title("MENU ĐIỀU HƯỚNG")
    st.info("Phân tích Mạng xã hội")

    # Nút Trang chủ
    if st.button("🏠 Trang chủ", use_container_width=True):
        st.session_state.page = "Trang chủ"

    st.markdown("---")
    st.markdown("### Chức năng chính")

    if st.button("1. Tìm kiếm & Phân tích", use_container_width=True):
        st.session_state.page = "TimKiem_PhanTich"

    if st.button("2. Dự đoán & Khám phá", use_container_width=True):
        st.session_state.page = "DuDoan_KhamPha"

    st.markdown("---")
    st.caption(
        "**Thực hiện bởi Nhóm 3:**\n\n"
        "👤 **Quân:** Extractor (Data)\n\n"
        "👤 **Tân:** Transformer (AI)\n\n"
        "👤 **Quang:** App Lead (Dev)"
    )
if st.session_state.page == "Trang chủ":
    writer("# Chào mừng đến với Hệ thống Phân tích Mạng xã hội",speed=0.02)
    writer("""
    Dự án này sử dụng dữ liệu từ **Wikidata** để xây dựng một đồ thị khổng lồ kết nối các nhân vật nổi tiếng.

    👈 **Hãy chọn một chức năng từ thanh bên trái để bắt đầu.**
    """, speed=0.008)
    time.sleep(0.5)
    st.image("https://dist.neo4j.com/wp-content/uploads/example-viz.png",
        caption="Mô phỏng đồ thị mạng xã hội")

elif st.session_state.page == "TimKiem_PhanTich":
    writer("# 1. Tìm kiếm và Dự đoán",speed=0.03)
    tab1, tab2 = st.tabs([
        "✈️ Sáu Bậc Xa cách",
        "📈 Phân tích mạng lưới"
    ])

    with tab1:
        render_tab_bfs()
    with tab2:
        render_tab_analytics()

elif st.session_state.page == "DuDoan_KhamPha":
    writer("# 2. Dự đoán và Khám phá", speed=0.03)
    tab1, tab2 = st.tabs([
        "🔮 Dự đoán liên kết",
        "🔍 Khám phá Lân cận"
    ])

    with tab1:
        render_tab_ai()
    with tab2:
        render_tab_ego()








