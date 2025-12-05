import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data_output"

RAW_DIR = DATA_DIR / "raw"
GRAPH_DIR = DATA_DIR / "graph"
TRAINING_DIR = DATA_DIR / "training"
MODELS_DIR = DATA_DIR / "models"

for d in [DATA_DIR, RAW_DIR, GRAPH_DIR, TRAINING_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


GRAPH_PATH = GRAPH_DIR / "G_full.gpickle"


SEARCH_INDEX_PATH = GRAPH_DIR / "search_index.json"
ANALYTICS_PATH = GRAPH_DIR / "analytics.json"


PYG_DATA_PATH = TRAINING_DIR / "processed_data.pt"
MAPPING_PATH = TRAINING_DIR / "mappings.pkl"

MODEL_PATH = MODELS_DIR / "model.pth"

TRAINING_HISTORY_PATH = DATA_DIR / "training_history.json"

SPARQL_TIMEOUT = 300
DEFAULT_PAGE_SIZE = 5000
INPUT_DIM = 385
HIDDEN_DIM = 64
OUTPUT_DIM = 32
LEARNING_RATE = 0.01
EPOCHS = 100
BATCH_SIZE = 128
FUZZY_THRESHOLD = 60.0