import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_DIR))

from config import GRAPH_PATH, RAW_DIR, QueryTemplates
from infrastructure.pipelines import GraphTransformer, WikidataExtractor
from infrastructure.repositories import PickleGraphRepository


def run_etl_pipeline():
    extractor = WikidataExtractor(user_agent= 'quangminh222@gmail.com')
    success = extractor.fetch_all_relationships()
    if not success:
        print('Failed to fetch data from Wikidata.')
        return
    transformer = GraphTransformer()
    files_config = [
        (str(RAW_DIR / "raw_data_spouse.json"), "person", "spouse"),
        # ... các file khác
    ]

    G_final = transformer.build_full_graph(files_config)

    repo = PickleGraphRepository(GRAPH_PATH)

    success = repo.save_graph(G_final)

    if success:
        print("✅ ETL Pipeline hoàn tất thành công!")
    else:
        print("❌ Lưu thất bại!")


if __name__ == "__main__":
    run_etl_pipeline()