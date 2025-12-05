# Phân tích Mạng xã hội (Wikidata) & Dự đoán Mối liên kết AI

**Dự án của Nhóm:**
* **Quân:** Kỹ sư Wikidata (Extractor / SPARQL).
* **Tân:** Kỹ sư Đồ thị & AI (Transformer / AI Lead).
* **Quang:** Kỹ sư Module & Ứng dụng (Loader / App Lead).



---

## 1. 📜 Giới thiệu Dự án (Project Manifesto)

Dự án này là một ứng dụng Khoa học Dữ liệu End-to-End, thực hiện việc xây dựng và phân tích mạng lưới liên kết xã hội của những người nổi tiếng (bao gồm diễn viên, chính trị gia, nhạc sĩ...). 

Dự án này sử dụng nguồn dữ liệu phong phú từ **Wikidata** (một cơ sở tri thức mở) và ngôn ngữ truy vấn **SPARQL** để xây dựng một đồ thị phức tạp với nhiều loại quan hệ.

Dự án giải quyết hai mục tiêu chính:

1.  **Module 1: Phân tích "Sáu Bậc Xa cách" (Mô tả)**
    * Xây dựng một đồ thị mạng lưới đa quan hệ.
    * Triển khai thuật toán **Tìm kiếm theo Chiều rộng (BFS)** để tìm và trực quan hóa đường đi ngắn nhất (số "bậc" xa cách) giữa hai nhân vật bất kỳ.

2.  **Module 2: Dự đoán Mối liên kết (Dự đoán)**
    * Sử dụng kỹ thuật "giấu cạnh" (edge masking) để tạo bộ dữ liệu huấn luyện.
    * Xây dựng mô hình **Machine Learning (Random Forest)** để dự đoán xác suất hai nhân vật *chưa từng* liên kết sẽ có một liên kết mới, dựa trên các đặc trưng cấu trúc đồ thị.

## 2. 🛠️ Ngăn xếp Công nghệ (Tech Stack)

Đây là các công cụ và thư viện chính được sử dụng trong dự án:

* **Ngôn ngữ:** Python 3.9+
* **Thu thập Dữ liệu (ETL):** `SPARQLWrapper` (để gọi Wikidata), `Pandas`
* **Phân tích & Xử lý Đồ thị:** `NetworkX`
* **Huấn luyện AI/ML:** `Scikit-learn`
* **Ứng dụng Web (Demo):** `Streamlit`
* **Trực quan hóa Đồ thị:** `Pyvis`
* **Quản lý Mã nguồn:** `Git` & `GitHub`



## 3. 🏗️ Kiến trúc Dự án

Dự án được xây dựng theo kiến trúc 3 tầng rõ rệt:

1.  **Tầng Dữ liệu (Data Layer):**
    * Một pipeline ETL (Extract-Transform-Load) được xây dựng để gọi API của Wikidata (dùng SPARQL), làm sạch và nạp vào một đối tượng đồ thị `NetworkX` (`G_full.gpickle`).
2.  **Tầng Logic (Logic Layer):**
    * **Module 1 (BFS):** `src/module_1_bfs.py` (Quang) chứa logic `nx.shortest_path` để tìm đường đi.
    * **Module 2 (AI):** `src/ai_utils.py` và `train.py` (Tân) chứa toàn bộ logic AI, từ tạo mẫu đến dự đoán.
3.  **Tầng Trình diễn (Presentation Layer):**
    * `src/app.py` (Quang) là một ứng dụng Streamlit, đóng vai trò là giao diện người dùng (UI) để tương tác với 2 module logic.

## 4. 🔬 Phương pháp luận (Methodology)

### A. Giai đoạn 1: Xây dựng Đồ thị (ETL)

1.  **Extract (Quân):** Sử dụng `SPARQLWrapper` để thực thi nhiều truy vấn SPARQL (đã tối ưu, bỏ `LIMIT`) lên endpoint của Wikidata. Các quan hệ được lấy bao gồm (nhưng không giới hạn):
    * `wdt:P26` (Vợ/chồng)
    * `wdt:P69` (Học tại)
    * `wdt:P102` (Đảng phái chính trị)
    * ... (và các quan hệ khác)
    * Kết quả trả về là nhiều file `raw_..._FINAL.json`.

2.  **Transform (Tân):** Viết script `graph_builder.py` để:
    * Đọc và "làm phẳng" (dùng `pandas.json_normalize`) các file JSON thô.
    * Khởi tạo một đồ thị `G_full = nx.Graph()`.
    * **Xử lý (1-1):** Với quan hệ "vợ/chồng", thêm cạnh trực tiếp `G_full.add_edge(A, B, relationship="spouse")`.
    * **Xử lý (N-N):** Với quan hệ "học tại", dùng `pandas.groupby('school_id')` để tìm các nhóm sinh viên. Lặp 2 vòng `for` trong mỗi nhóm để thêm cạnh `G_full.add_edge(Student_A, Student_B, relationship="school")`.
    * (Tương tự cho các quan hệ N-N khác).

3.  **Load (Tân/Quang):**
    * Tân lưu đồ thị cuối cùng: `nx.write_gpickle(G_full, "G_full.gpickle")`.
    * Quang nạp file này trong `module_1_bfs.py`.

### B. Module 1: Phân tích "Sáu Bậc Xa cách" (BFS)

1.  **Nạp Đồ thị:** `G = nx.read_gpickle("G_full.gpickle")`.
2.  **Tìm ID:** Viết hàm `get_person_id(G, name)` để chuyển tên người dùng nhập (string) thành ID của node (ví dụ: "Q123"). Hàm này phải chuẩn hóa (`.lower()`) để tìm kiếm.
3.  **Thuật toán:** Sử dụng hàm `networkx.shortest_path(G, source_id, target_id)`. Bên dưới, hàm này triển khai thuật toán **Tìm kiếm theo Chiều rộng (BFS)**, đảm bảo tìm ra đường đi có số "bậc" (số cạnh) ít nhất.
4.  **Kết quả:** Trả về một danh sách tên, đại diện cho chuỗi liên kết.

### C. Module 2: AI Dự đoán Mối liên kết (ML)

Đây là một bài toán **Phân loại Nhị phân (Binary Classification)** trên đồ thị: "Liệu một cạnh (A, B) chưa tồn tại có khả năng xuất hiện trong tương lai hay không?" (Nhãn 1 = Có, Nhãn 0 = Không).

**1. Tạo Bộ dữ liệu (Bằng kỹ thuật "Giấu Cạnh"):**
* **Load `G_full`**.
* **Tạo Mẫu Dương (y=1):** Lấy ngẫu nhiên 10% số cạnh *đang có* và "giấu" đi (`positive_samples = random.sample(G_full.edges(), 10%)`).
* **Tạo `G_train`:** Tạo một bản sao của `G_full` và xóa các Mẫu Dương đi (`G_train.remove_edges_from(positive_samples)`). Đây là đồ thị "bị thủng" mà AI sẽ thấy.
* **Tạo Mẫu Âm (y=0):** Lấy ngẫu nhiên các cặp *không có cạnh* (dùng `nx.non_edges(G_full)`) với số lượng bằng Mẫu Dương.

**2. Trích xuất Đặc trưng (Feature Engineering):**
Với mỗi cặp (A, B) trong bộ dữ liệu (cả Âm và Dương), chúng tôi trích xuất các đặc trưng cấu trúc từ **`G_train`** (đồ thị "bị thủng"):

* `jaccard_coefficient`: (Số hàng xóm chung) / (Tổng số hàng xóm của cả A và B).
* `adamic_adar_index`: Đánh giá cao các hàng xóm chung "hiếm" (có ít liên kết).
* `preferential_attachment`: (Số hàng xóm của A) * (Số hàng xóm của B).



**3. Huấn luyện Mô hình:**
* Sử dụng `train_test_split` để chia bộ dữ liệu đặc trưng.
* Huấn luyện mô hình **Random Forest Classifier** (`scikit-learn`) để dự đoán nhãn (0 hoặc 1).
* Lưu mô hình đã huấn luyện (`model.pkl`).

## 5. 📊 Kết quả (Results) & Demo

Chúng tôi đã tích hợp thành công cả hai module vào một ứng dụng Streamlit.

* **Module 1 (BFS):** Hệ thống có khả năng tìm thấy đường đi ngắn nhất giữa hàng chục ngàn nhân vật trong cơ sở dữ liệu Wikidata.
    
* **Module 2 (AI):** Mô hình AI đạt được độ chính xác (AUC-ROC) là **XX.X%** (điền kết quả của nhóm) trên tập kiểm thử (test set), chứng tỏ khả năng dự đoán tốt hơn đáng kể so với đoán ngẫu nhiên.
    

## 6. 🚀 Hướng dẫn Cài đặt & Chạy (Setup & Run)

Đây là các bước để chạy dự án này trên máy của bạn.

### A. Yêu cầu Tiên quyết
* Python 3.9+
* Git

### B. Cài đặt

1.  **Clone (Tải về) kho chứa:**
    ```bash
    git clone [https://github.com/](https://github.com/)minhquang0407/Social-Link-Prediction.git
    cd Social-Link-Prediction
    ```

2.  **Tạo môi trường ảo (Khuyến nghị):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Trên Windows: .\.venv\Scripts\activate
    ```

3.  **Cài đặt thư viện:**
    ```bash
    pip install -r requirements.txt
    ```

*(Lưu ý: Nếu dùng API Key, hãy tạo file `.env` và thêm vào `.gitignore`)*

### C. Chạy Dự án

#### Bước 1: Chạy Pipeline Dữ liệu (Chỉ chạy 1 lần)
*(Lưu ý: Bước này sẽ mất nhiều giờ/ngày để lấy dữ liệu và xây dựng đồ thị)*

1.  **Chạy script của Quân (Extractor):**
    ```bash
    python data_pipeline/wikidata_collector.py
    ```
    *(Chờ... script này chạy rất lâu. Sẽ tạo ra các file `data_output/raw_..._FINAL.json`)*

2.  **Chạy script của Tân (Transformer):**
    ```bash
    python data_pipeline/graph_builder.py
    ```
    *(Chờ... Sẽ tạo ra file `data_output/G_full.gpickle`)*

#### Bước 2: Huấn luyện Mô hình AI (Chỉ chạy 1 lần)

```bash
python src/train.py
