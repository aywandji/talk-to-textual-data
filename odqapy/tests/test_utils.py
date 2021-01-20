import os
from os.path import dirname, abspath
import shutil
import glob
from unittest.mock import Mock
import json

import pytest
from transformers import AutoTokenizer
from transformers import TFAutoModelForQuestionAnswering

from odqapy.db import DataBaseClient
from odqapy.retriever import DocumentRetriever
from odqapy.index import DocumentIndex, IndexBuildingException
from odqapy.reader import DocumentReader

DATA_DIR = os.path.join(dirname(abspath(__file__)), "test_data/")


@pytest.fixture
def db_inputs():
    path_to_database_file = DATA_DIR + "db/path_to_db_test.db"
    return path_to_database_file


@pytest.fixture
def index_inputs():
    path_to_index_dir = DATA_DIR + "path_to_index_dir/"
    index_type = "tf_idf_sklearn"
    nltk_data_path = "../../data/ext_data/nltk_data/"
    return path_to_index_dir, index_type, nltk_data_path


@pytest.fixture
def database_client(db_inputs):
    path_to_database_file = db_inputs
    db_client = DataBaseClient(path_to_database_file)
    # add docs to db for testing purpose
    # (there is already one default doc in DATA_DIR)
    new_doc_path = DATA_DIR + "json_test.json"
    with open(new_doc_path, "w+") as json_file:
        json.dump({"url": "url1", "title": "title1",
                   "text": "text for the new document is here"}, json_file)
    docs_file_paths = glob.glob(DATA_DIR + "*.json")
    db_client.add_documents(docs_file_paths)
    yield db_client

    try:
        os.remove(path_to_database_file)
        os.remove(new_doc_path)
    except OSError as error:
        print("Error: %s : %s" % (path_to_database_file, error.strerror))


class TestDocumentIndex:
    @pytest.fixture
    def document_index(self, index_inputs, database_client):
        path_to_index_dir, index_type, nltk_data_path = index_inputs
        yield DocumentIndex(path_to_index_dir, database_client, index_type,
                            nltk_data_path=nltk_data_path)

        try:
            shutil.rmtree(path_to_index_dir)
        except OSError as error:
            print("Error: %s : %s" % (path_to_index_dir, error.strerror))

    def test_init_create_index(self, document_index, index_inputs):
        path_to_index_dir, index_type, _ = index_inputs

        assert document_index.index_type == index_type
        assert document_index.path_to_index_dir == path_to_index_dir
        assert document_index.path_to_index_file == os.path.join(
            path_to_index_dir, index_type+".index")
        assert document_index.doc_vectorizer is not None
        assert document_index.all_documents_sparse_vectors is not None

    def test_load_index(self, document_index):
        document_index.doc_vectorizer = None
        document_index.all_documents_sparse_vectors = None
        document_index._load_index()

        assert document_index.doc_vectorizer is not None
        assert document_index.all_documents_sparse_vectors is not None

    def test_index_building_exception(self, index_inputs):
        _, _, nltk_data_path = index_inputs
        with pytest.raises(IndexBuildingException):
            _ = DocumentIndex(DATA_DIR + "random_path/", None,
                              nltk_data_path=nltk_data_path)

    def test_query_similar_document_ids(self, database_client, document_index):
        doc_1 = database_client.get_documents([1])[0]
        doc_2 = database_client.get_documents([2])[0]
        for i, doc in enumerate([doc_1, doc_2]):
            res = document_index.query_similar_document_ids(
                doc["text"], nb_docs=2)
            _, similar_docs_scores = res
            # get the  most similar doc
            most_similar_doc_id = None
            max_score = -1
            for doc_id, doc_score in similar_docs_scores.items():
                if doc_score > max_score:
                    most_similar_doc_id = doc_id

            assert most_similar_doc_id == i+1


class TestDocumentRetriever:

    @pytest.fixture
    def document_retriever(self, index_inputs, db_inputs, database_client):
        # request database_client to keep db file  filled.
        path_to_index_dir, _, nltk_data_path = index_inputs
        path_to_database_file = db_inputs
        return DocumentRetriever(path_to_index_dir, path_to_database_file,
                                 nltk_data_path=nltk_data_path)

    def test_init(self, document_retriever):
        assert isinstance(document_retriever.db_client, DataBaseClient)
        assert isinstance(document_retriever.document_index, DocumentIndex)

    def test_process_query(self, document_retriever):
        query = "query hello !"

        assert document_retriever.process_query(query) == query

    def test_query_related_documents(self, document_retriever):
        # should test result accuracy
        query = "query hello !"
        nb_docs = 1
        results = document_retriever.query_related_documents(query, nb_docs)

        assert len(results) <= nb_docs
        all_keys = list(results[0].keys())
        for field in ["text", "score", "title", "url"]:
            assert field in all_keys


class TestDocumentReader:
    @pytest.fixture
    def doc_reader_inputs(self):
        huggingface_model_name = "test-distilbert-base-uncased-distilled-squad"
        test_models_dir = DATA_DIR + "test_models/"
        return huggingface_model_name, test_models_dir

    @pytest.fixture
    def document_reader(self, doc_reader_inputs, monkeypatch):
        model_name, test_models_dir = doc_reader_inputs
        # Setup mocks

        def create_file_with_name(file_name):
            def create_file(model_path):
                with open(os.path.join(model_path, file_name), "w") as f:
                    f.write("model file")
            return create_file

        def create_cache_dir(model_name_path, cache_dir="cache_dir"):
            if (not os.path.isdir(model_name_path)) & (not os.path.isdir(cache_dir)):
                os.mkdir(cache_dir)

            returned_object = Mock()
            returned_object.save_pretrained.side_effect = create_file_with_name(
                "model.h5")
            return returned_object

        monkeypatch.setattr(AutoTokenizer, "from_pretrained", create_cache_dir)
        monkeypatch.setattr(TFAutoModelForQuestionAnswering,
                            "from_pretrained", create_cache_dir)

        doc_reader = DocumentReader(model_name, test_models_dir)
        yield doc_reader

        try:
            shutil.rmtree(test_models_dir)
        except OSError as error:
            print("Error: %s : %s" % (test_models_dir, error.strerror))

    def test_init_load_model(self, document_reader, doc_reader_inputs):
        huggingface_model_name, models_dir = doc_reader_inputs
        model_dir_path = os.path.join(
            models_dir, huggingface_model_name.replace("-", "_"))

        assert document_reader.model_path == model_dir_path
        assert document_reader.model_name == huggingface_model_name
        assert os.path.isdir(model_dir_path)
        assert len(glob.glob(model_dir_path+"/*.h5")) > 0
        assert document_reader.tokenizer is not None
        assert document_reader.model is not None

    # def test_read_answer(self,document_reader):
    #     question = "who is the author ?"
    #     contexts = [{"The author is Jake lane"}]
    #     answers = document_reader.read_answer(question, contexts)
    #     assert len(answers) == len(contexts)
    #     assert document_reader.model.iscalled()
    #     # for answer in answers:
    #     #     assert "Jake" in
