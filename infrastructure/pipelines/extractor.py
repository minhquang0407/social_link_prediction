import sys
import json
import os
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_DIR))
from datetime import datetime
from SPARQLWrapper import SPARQLWrapper, JSON
from config.queries import ALL_QUERIES, BASE_QUERY
from config.settings import RAW_DIR

# hàm ghi log
def log_query_info(file_name, total_count, log_file="query_log.txt"):
    """
    Ghi log thông tin truy vấn vào file văn bản (.txt).
    Định dạng: "{query_name} đã truy vấn {total_count} kết quả, hoàn thành lúc {time}"
    """
    now = datetime.now()
    timestamp_str = now.strftime("%H:%M:%S %d/%m/%Y")

    log_message = f"{file_name} đã truy vấn {total_count} kết quả, hoàn thành lúc {timestamp_str}\n"

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_message)
        print(f"--> [LOG] Đã ghi thông tin vào '{log_file}'")
    except Exception as e:
        print(f"Lỗi khi ghi log txt: {e}", file=sys.stderr)
# ---------------------------------------------------
class WikidataExtractor:

    def __init__(self, user_agent):
        if not user_agent:
            raise ValueError("User-Agent là bắt buộc để truy vấn Wikidata.")

        self.endpoint_url = "https://query.wikidata.org/sparql"
        self.sparql = SPARQLWrapper(self.endpoint_url)
        self.sparql.agent = user_agent
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(300)
        self.current_json_head = None
        self.step = 2

    def _run_paginated_query(self, base_query: str, page_size=10000) -> list:

        page = 1
        all_bindings = []
        retry_count = 0
        offset_num = 0
        max_retries = 20
        current_page_size = page_size

        while True:
            paginated_query = base_query + f"\nLIMIT {current_page_size}\nOFFSET {offset_num}"
            self.sparql.setQuery(paginated_query)

            print(f"{datetime.now().strftime('%H:%M:%S')} Đang lấy trang {page}, {current_page_size}/page...", end="",
                  flush=True)

            try:
                start_time = time.monotonic()

                # Truy vấn và decode
                response = self.sparql.query()
                raw_data_bytes = response.response.read()
                cleaned_data_string = raw_data_bytes.decode('utf-8', errors='ignore')  # Dùng 'ignore' cho an toàn
                results = json.loads(cleaned_data_string)

                end_time = time.monotonic()
                duration = end_time - start_time

                if self.current_json_head is None:
                    self.current_json_head = results["head"]
                bindings = results["results"]["bindings"]

                retry_count = 0

                all_bindings.extend(bindings)

                print(f" OK! Lấy {len(bindings)}, mất {int(duration)}s", end="\n", flush=True)

                if not bindings or len(bindings) < current_page_size:
                    print(f"\n-------> Đã lấy hết! Tổng {len(all_bindings)}")
                    break

                page += 1
                offset_num += current_page_size
                time.sleep(1)

            except Exception as e:
                print(f"\n!!! LỖI KHI ĐANG TRUY VẤN (offset {offset_num}): {e}", file=sys.stderr)
                retry_count += 1

                if retry_count > max_retries:
                    print(f"    Đã thử lại {max_retries} lần thất bại. TỪ BỎ truy vấn này.", file=sys.stderr, flush = True)
                    break
                else:
                    if retry_count % 5 == 0 and retry_count > 0:
                        sleep_time = 10 * (retry_count // 5)
                    else:
                        sleep_time = 5 * retry_count

                    if current_page_size > 2000:
                        current_page_size -= 2000

                    print(
                        f"    Đang thử lại (lần {retry_count}/{max_retries}) sau {sleep_time}s với {current_page_size}/page...",
                        file=sys.stderr)
                    time.sleep(sleep_time)

        return all_bindings

    def _create_intervals(self,start_val, end_val) -> list:
        intervals = []
        current_start = start_val
        while current_start < end_val:
            current_end = current_start + self.step
            if current_end > end_val:
                current_end = end_val
            intervals.append((current_start, current_end))
            current_start = current_end
        return intervals

    def _run_interval_query(self, start, end, base_query, page_size) -> list:
        """
        Chạy query theo từng khoảng thời gian (Intervals).
        """
        self.current_json_head = None  # thiết lập lại json_head trước khi chạy
        all_bindings = []
        intervals = self._create_intervals(start, end + 1)

        print(f"=========== BẮT ĐẦU CHẠY THEO KHOẢNG {start}-{end} ===========")
        start_time = datetime.now()

        for start_year, end_year in intervals:
            print(f"\n--- KỶ NGUYÊN {start_year}-{end_year} ---")

            year_filter_str = f"FILTER(YEAR(?person_dob) > {start_year} && YEAR(?person_dob) <= {end_year})"
            era_query = base_query.replace("##YEAR_FILTER_HOOK##", year_filter_str)

            binding = self._run_paginated_query(era_query, page_size)
            all_bindings.extend(binding)

            print(f"--- KẾT THÚC {start_year}-{end_year}. (Tổng tích lũy: {len(all_bindings)}) ---")

        end_time = datetime.now()
        print(f"========== TỔNG KẾT: {len(all_bindings)} kết quả, Thời gian: {end_time - start_time} ========== ")

        return all_bindings


    def _save_data(self, all_bindings, name, output_dir="data"):
        # đường dẫn cho file lưu truy vấn
        output_filename = os.path.join(output_dir, f"raw_data_{name}.json")
        # đường dẫn cho file ghi log
        log_file_path = os.path.join(output_dir, "query_log.txt")

        head_data = self.current_json_head if self.current_json_head else {"vars": []}
        final_json_output = {
            "head": head_data,
            "results": {"bindings": all_bindings}
        }

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(final_json_output, f, ensure_ascii=False, indent=2)
            print(f"\n==> ĐÃ LƯU: {len(all_bindings)} kết quả vào file '{output_filename}'")
            # ghi log
            log_query_info(output_filename, len(all_bindings), log_file_path)
        except IOError as e:
            print(f"\n!!! LỖI KHI LƯU FILE: {e}", file=sys.stderr)


    def fetch_all_relationships(self, relationship_queries, start, end, output_dir="data"):
        os.makedirs(output_dir, exist_ok=True)
        for name, (snippet, page_size) in relationship_queries.items():

            print(f"\n\n################ STARTING JOB: {name} ################")
            full_query =BASE_QUERY.replace("##FIND_HOOK##", snippet) # thêm truy vấn  con
            all_bindings = self._run_interval_query(start, end, full_query, page_size) # chạy truy vấn

            self._save_data(all_bindings, name, output_dir)  # lưu kết quả

            time.sleep(1)

        print("\n*** HOÀN TẤT TẤT CẢ TRUY VẤN! ***")


if __name__ == "__main__":
    YOUR_USER_AGENT = "SocialLinkPredictionBot/1.0 (naqaq2005@gmail.com)"

    extractor = WikidataExtractor(user_agent=YOUR_USER_AGENT)
    extractor.fetch_all_relationships(ALL_QUERIES, 1800, 2025, str(RAW_DIR))
