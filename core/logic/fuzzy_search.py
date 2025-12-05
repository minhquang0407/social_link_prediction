from core.interfaces import ISearchEngine
from rapidfuzz import process, fuzz, utils
from unidecode import unidecode


class RapidFuzzySearch(ISearchEngine):
    def __init__(self, search_index_data):

        if search_index_data:
            self.search_map, self.all_keys = search_index_data
        else:
            self.search_map, self.all_keys = {}, []

    def search_best(self, query: str, threshold=60):
        """
        Thực thi tìm kiếm mờ.
        """
        if not query: return None, 0

        try:
            # Chuẩn hóa input người dùng ngay lúc tìm kiếm
            clean_input = unidecode(str(query)).lower()

            # Dùng RapidFuzz để so khớp với danh sách keys
            result = process.extractOne(
                clean_input,
                self.all_keys,
                scorer=fuzz.token_set_ratio,
                processor=utils.default_process
            )

            if result:
                best_key, score, _ = result

                if score >= threshold:
                    people_list = self.search_map[best_key]

                    # Trả về người đầu tiên trong danh sách (hoặc logic chọn người nổi tiếng nhất)
                    return people_list[0], score

        except Exception as e:
            print(f"Lỗi tìm kiếm: {e}")
            pass

        return None, 0

