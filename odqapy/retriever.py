import time

from .db import DataBaseClient
from .index import DocumentIndex


class DocumentRetriever:
    def __init__(self, index_path, database_path, nltk_data_path):
        self.db_client = DataBaseClient(database_path)
        self.document_index = DocumentIndex(index_path, self.db_client,
                                            nltk_data_path=nltk_data_path)

    def process_query(self, query):

        return query

    def query_related_documents(self, query, nb_docs=1):
        """returned documents related to query

        Args:
            query (str): raw input document
            nb_docs (int, optional): Max number of documents to return. Defaults to 1.

        Returns:
            list: list of similar documents
        """
        start_time = time.time()

        processed_query = self.process_query(query)
        similar_documents_ids, similar_documents_scores = self.document_index.query_similar_document_ids(
            processed_query, nb_docs)
        similar_documents = self.db_client.get_documents(similar_documents_ids)
        for doc in similar_documents:
            doc["score"] = similar_documents_scores[doc["id"]]

        print("document retriever query_related_documents ends after {} seconds".format(
            time.time()-start_time))
        print("-"*30)

        return similar_documents
