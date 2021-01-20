import os
from os.path import dirname, abspath
import json
import glob

import pytest

from odqapy.db import DataBaseClient

DATA_DIR = os.path.join(dirname(abspath(__file__)), "test_data/")

@pytest.fixture
def db_inputs():
    return DATA_DIR + "db/path_to_db_test.db"

@pytest.fixture
def doc_to_add():
    doc_path = glob.glob(DATA_DIR + "*.json")[0]
    with open(doc_path) as doc_file:
        document_dict = json.load(doc_file)
    return document_dict, doc_path

@pytest.fixture
def database_client(db_inputs):
    path_to_database_file = db_inputs
    db_client = DataBaseClient(path_to_database_file)
    yield db_client

    try:
        os.remove(path_to_database_file)
    except OSError as error:
        print("Error: %s : %s" % (path_to_database_file, error.strerror))

class TestDataBaseClient:
    def test_init(self, database_client, db_inputs):
        path_to_database_file = db_inputs
        assert database_client.db_file_path == path_to_database_file

    # def test_documents_generator(self, database_client, doc_to_add):
    #     document_dict, doc_path = doc_to_add
    #     for doc in database_client._documents_generator([doc_path]):
    #         assert doc[0] == document_dict["title"]
    #         assert doc[1] == document_dict["text"]
    #         assert doc[2] == document_dict["url"]


    def test_get_add_documents(self,database_client,doc_to_add):
        document_dict, doc_path = doc_to_add
        database_client.add_documents([doc_path])

        docs = database_client.get_documents(None) ##get all docs
        assert document_dict["title"] == docs[0]["title"]
        assert document_dict["text"] == docs[0]["text"] 
        assert document_dict["url"] == docs[0]["url"] 

        docs = database_client.get_documents([1]) ## doc by doc_id
        assert document_dict["title"] == docs[0]["title"]
        assert document_dict["text"] == docs[0]["text"]
        assert document_dict["url"] == docs[0]["url"]


