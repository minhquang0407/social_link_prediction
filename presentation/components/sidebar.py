import streamlit as st


def render_sidebar():
    """
    Hàm vẽ thanh điều hướng bên trái (Sidebar).
    Sử dụng st.session_state.page để điều hướng.
    """
    with st.sidebar:
        st.title("MENU ĐIỀU HƯỚNG")
        st.info("Đồ án KLTN - Phân tích Mạng xã hội")

        # Nút Trang chủ
        if st.button("🏠 Trang chủ", use_container_width=True):
            st.session_state.page = "HOME"

        st.markdown("---")
        st.markdown("### Chức năng chính")

        # Nút Chức năng 1
        if st.button("1. Tìm kiếm & Phân tích", use_container_width=True):
            st.session_state.page = "SEARCH"

        # Nút Chức năng 2
        if st.button("2. Dự đoán & Khám phá", use_container_width=True):
            st.session_state.page = "AI"

        st.markdown("---")
        st.caption(
            "**Thực hiện bởi Nhóm 3:**\n\n"
            "👤 **Quân:** Extractor (Data)\n\n"
            "👤 **Tân:** Transformer (AI)\n\n"
            "👤 **Quang:** App Lead (Dev)"
        )