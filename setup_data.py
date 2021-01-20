import os
from os.path import dirname, abspath
import sys
import glob
import shutil

from odqapy.db import DataBaseClient
from odqapy.index import DocumentIndex
from odqapy.reader import DocumentReader

DATA_FOLDER = os.path.join(dirname(abspath(__file__)), "data/")
EXT_DATA = DATA_FOLDER + "ext_data/"
ODQA_DATA = DATA_FOLDER + "odqa_data/"
NLTK_DATA_DIR = EXT_DATA + "nltk_data/"
WEBSITES_DIR = EXT_DATA + "websites/"
DB_DIR = ODQA_DATA + "db/"
DB_FILE_PATH = os.path.join(DB_DIR, "odqa.db")
DOCS_INDEX_DIR = ODQA_DATA + "docs_index/"
DOCUMENTS_DIR = ODQA_DATA + "documents/"
QA_MODELS_DIR = ODQA_DATA + "qa_models/"
QA_MODEL_NAME = "distilbert-base-uncased-distilled-squad"


def check_directory(dir_path):
    """Check if directory exists

    Args:
        dir_path (str): path to directory
    """
    if not os.path.isdir(dir_path):
        # create dir and all intermediates if they don't exist
        os.makedirs(dir_path, exist_ok=True)


def setup_database_and_index():
    """Check if database and index exist. If not, create it
    """
    documents_paths = glob.glob(DOCUMENTS_DIR+"*.json")
    if len(documents_paths) != 0:
        db_client = DataBaseClient(DB_FILE_PATH)
        db_client.add_documents(documents_paths)

        _ = DocumentIndex(DOCS_INDEX_DIR, db_client,
                          nltk_data_path=NLTK_DATA_DIR)
    else:
        sys.exit(f"No json document found at {DOCUMENTS_DIR}. Add documents and run me again. \n")
        # print(
        #     "-"*30, f"No json document found at {DOCUMENTS_DIR}. Add documents and run me again. \n", "-"*30)


def check_qa_model_data():
    """Initialize DocumentReader to check and
        download (if needed) model data
    """
    _ = DocumentReader(model_name=QA_MODEL_NAME,
                       models_dir=QA_MODELS_DIR)


def reinitialize(dir_list):
    """Delete all data for each dir in dir_list

    Args:
        dir_list (List): list of directories paths to delete
    """
    for dirpath in dir_list:
        if os.path.isdir(dirpath):
            print(f"deleting folder {dirpath}")
            shutil.rmtree(dirpath)


if __name__ == "__main__":
    # Uncomment the line below if you want to clean data
    reinitialize([DB_DIR, DOCS_INDEX_DIR])

    check_directory(WEBSITES_DIR)
    check_directory(DB_DIR)
    check_directory(DOCS_INDEX_DIR)
    check_directory(DOCUMENTS_DIR)
    check_directory(QA_MODELS_DIR)

    setup_database_and_index()
    check_qa_model_data()
