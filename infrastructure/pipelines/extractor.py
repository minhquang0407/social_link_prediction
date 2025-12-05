import sys
import json
import time
from datetime import datetime
from SPARQLWrapper import SPARQLWrapper, JSON
from pathlib import Path
FILE_PATH = Path(__file__).resolve()
PROJECT_DIR = FILE_PATH.parent.parent.parent
sys.path.append(str(PROJECT_DIR))
from config import BASE_QUERY, ALL_QUERY
from config import RAW_DIR, SPARQL_TIMEOUT


class WikidataExtractor:
    @staticmethod
    def save_data(all_bindings, name, output_dir):
        base_path = Path(output_dir)
        base_path.mkdir(parents=True, exist_ok=True)
        output_filename = base_path / f"raw_data_{name}.json"
        final_json_output = {
            "head": {"vars": []},
            "results": {"bindings": all_bindings}
        }

        try:
            with open(str(output_filename), 'w', encoding='utf-8') as f:
                json.dump(final_json_output, f, ensure_ascii=False, indent=2)
            print(f"\n==> ĐÃ LƯU: {len(all_bindings)} kết quả vào file '{output_filename}'")
        except IOError as e:
            print(f"\n!!! LỖI KHI LƯU FILE: {e}", file=sys.stderr)

        return output_filename
    def __init__(self, user_agent):
        if not user_agent:
            raise ValueError("User-Agent là bắt buộc để truy vấn Wikidata.")

        self.endpoint_url = "https://query.wikidata.org/sparql"
        self.sparql = SPARQLWrapper(self.endpoint_url)
        self.sparql.agent = user_agent
        self.sparql.setReturnFormat(JSON)
        self.sparql.setTimeout(SPARQL_TIMEOUT)

    def _run_basic_query(self, query: str, page_size=10000) -> list:

        page = 1
        all_bindings = []
        json_head = None
        retry_count = 0
        offset_num = 0
        max_retries = 30
        current_page_size = page_size 

        while True:
            paginated_query = query + f"\nLIMIT {current_page_size}\nOFFSET {offset_num}"
            self.sparql.setQuery(paginated_query)
            
            print(f"{datetime.now().strftime('%H:%M:%S')} Đang lấy trang {page}, {current_page_size}/page...", end="", flush=True)
            
            try:
                start_time = time.monotonic()
                
                # Truy vấn và decode
                response = self.sparql.query()
                raw_data_bytes = response.response.read()
                cleaned_data_string = raw_data_bytes.decode('utf-8', errors='ignore') # Dùng 'ignore' cho an toàn
                results = json.loads(cleaned_data_string)
                
		
                end_time = time.monotonic()
                duration = end_time - start_time
                
                if json_head is None:
                    json_head = results["head"]
                bindings = results["results"]["bindings"]
                
                retry_count = 0
                current_page_size = page_size
                all_bindings.extend(bindings)
                
                if not bindings or len(bindings) < current_page_size:
                    print(f"\n-------> Đã lấy hết! Tổng {len(all_bindings)}")
                    break

                print(f" OK! Lấy {len(bindings)}, mất {int(duration)}s", end="\n", flush=True)
                
                page += 1
                offset_num += current_page_size
                time.sleep(1)

            except Exception as e:
                print(f"\n!!! LỖI KHI ĐANG TRUY VẤN (offset {offset_num}): {e}", file=sys.stderr)
                retry_count += 1
                
                if retry_count > max_retries:
                    print(f"    Đã thử lại {max_retries} lần thất bại. TỪ BỎ truy vấn này.", file=sys.stderr)
                    break
                else:
                    if retry_count % 5 == 0 and retry_count > 0:
                        sleep_time = 60 * (retry_count // 5)
                    else:
                        sleep_time = 5 * retry_count
                    
                    if current_page_size > 2000:
                        current_page_size -= 2000
                    
                    print(f"    Đang thử lại (lần {retry_count}/{max_retries}) sau {sleep_time}s với {current_page_size}/page...", file=sys.stderr)
                    time.sleep(sleep_time)
                    
        return all_bindings

    def _create_intervals(self, start_val, end_val, step=10) -> list:
        intervals = []
        current_start = start_val
        while current_start < end_val:
            current_end = current_start + step
            if current_end > end_val:
                current_end = end_val
            intervals.append((current_start, current_end))
            current_start = current_end
        return intervals


    def _run_paginated_query(self, start, end, query, page_size,step = 10) -> list:
        """
        Chạy query theo từng khoảng thời gian (Intervals).
        """
        all_bindings = []
        intervals = self._create_intervals(start, end + 1,step = step)
        
        print(f"=========== BẮT ĐẦU CHẠY THEO KHOẢNG {start}-{end} ===========")
        start_time = datetime.now()
        
        for start_year, end_year in intervals:
            print(f"\n--- KỶ NGUYÊN {start_year}-{end_year} ---")
            
            year_filter_str = f"FILTER(YEAR(?person_dob) > {start_year} && YEAR(?person_dob) <= {end_year})"
            era_query = query.replace("##YEAR_FILTER_HOOK##", year_filter_str)
            
            binding = self._run_basic_query(era_query, page_size)
            all_bindings.extend(binding)
            
            print(f"--- KẾT THÚC {start_year}-{end_year}. (Tổng tích lũy: {len(all_bindings)}) ---")
            
        end_time = datetime.now()
        print(f"========== TỔNG KẾT: {len(all_bindings)} kết quả, Thời gian: {end_time - start_time} ========== ")

        return all_bindings


    def fetch_all_relationships(self, start=1800, end = 2025, step = 5,output_path = RAW_DIR):

        all_data = {}

        for name, (snippet, page_size) in ALL_QUERY.items():
            
            print(f"\n\n################ STARTING JOB: {name} ################")
            full_query = BASE_QUERY.replace("##FIND_HOOK##", snippet)
            all_bindings = self._run_paginated_query(start, end, full_query, page_size,step)
            
            output_filename = WikidataExtractor.save_data(all_bindings, name, output_path)

            try:
                with open(output_filename, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    all_data[name] = loaded_data["results"]["bindings"]
            except Exception:
                all_data[name] = []
            
            time.sleep(5)

        print("\n*** HOÀN TẤT TẤT CẢ TRUY VẤN! ***")
        return all_data

