import os
from pathlib import Path
import time
import json

from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem import WordNetLemmatizer
import nltk
from nltk.corpus import wordnet
from joblib import dump, load
import numpy as np

class LemmaTokenizer:
    """Apply tokenization + lemmatization
    """

    def __init__(self):
        self.wnl = WordNetLemmatizer()
        # words tokenization + ignore punctuations and numerical values.
        self.tokenizer = TfidfVectorizer().build_tokenizer()

    def get_wordnet_pos(self, word):
        """Map POS tag to first character lemmatize() accepts"""
        tag = nltk.pos_tag([word])[0][1][0].upper()
        tag_dict = {"J": wordnet.ADJ,
                    "N": wordnet.NOUN,
                    "V": wordnet.VERB,
                    "R": wordnet.ADV}

        return tag_dict.get(tag, wordnet.NOUN)

    def __call__(self, doc):
        return [self.wnl.lemmatize(t, pos=self.get_wordnet_pos(t)) for t in self.tokenizer(doc)]


def check_nltk_data(nltk_data_path):
    """Check if nltk data exist at provided path. If not, download and save it

    Args:
        nltk_data_path (str): path to nltk data dir
    """
    nltk_data_available = os.path.isdir(nltk_data_path)
    nltk_data_available = nltk_data_available and len(
        os.listdir(nltk_data_path)) != 0

    if not nltk_data_available:
        print(f"Downloading nltk_data since {nltk_data_path} is empty")
        nltk.download('wordnet', download_dir=nltk_data_path)
        nltk.download('averaged_perceptron_tagger',
                        download_dir=nltk_data_path)
    else:
        print(f"Adding {nltk_data_path} to NLTK paths")

    nltk.data.path.append(nltk_data_path)

class IndexBuildingException(Exception):
    pass


class DocumentIndex:
    # TODO
    # - get a documents generator from database client and not the full set of documents
    # - for similar documents  query, use hashing system to speed up the queries if needed
    # - Before training TF-IDF, apply lemmatization to reduce vocabulary length
    def __init__(self, path_to_index_dir, db_client=None,
                 index_type="tf_idf_sklearn",
                 nltk_data_path="../data/ext_data/nltk_data/"):
        """Initialize an index instance and load it. If no index file exist, 
        create a new index using existing database (db_client)

        Args:
            path_to_index_dir (str): Path to the directory containing the index files
            db_client (object, optional): database client used to create index if needed. Defaults to None.
            index_type (str, optional): Index type to use. Defaults to "tf_idf_sklearn".

        Raises:
            IndexBuildingException: Exception raises when trying to create index with empty database
        """
        self.index_type = index_type
        self.path_to_index_dir = path_to_index_dir
        self.path_to_index_file = os.path.join(
            path_to_index_dir, index_type+".index")
        self.doc_vectorizer = None
        self.all_documents_sparse_vectors = None
        self.all_documents_ids = None

        check_nltk_data(nltk_data_path)

        if os.path.isfile(self.path_to_index_file):
            self._load_index()
        else:
            # query db to get docs
            if not os.path.isdir(self.path_to_index_dir):
                Path(self.path_to_index_dir).mkdir(parents=True, exist_ok=True)

            if db_client is not None:
                documents = db_client.get_documents()
            else:
                raise IndexBuildingException(
                    "There is no index file and database is empty, please fill it first.")

            if len(documents) == 0:
                raise IndexBuildingException(
                    "There is no index file and database is empty, please fill it first.")
            else:
                self._create_index(documents)

    def _load_index(self):
        """Load index in memory (documents vectors and document vectorizer)
        """
        start_time = time.time()

        print("Loading index from ", self.path_to_index_file)
        if self.index_type == "tf_idf_sklearn":

            with open(self.path_to_index_file) as json_file:
                index_json = json.load(json_file)

            self.doc_vectorizer = load(
                index_json.get("doc_tf_idf_vectorizer_path", None))
            self.all_documents_sparse_vectors = load(
                index_json.get("doc_term_tf_idf_weights_path", None))
            self.all_documents_ids = index_json.get("doc_db_ids", None)

        index_is_corrupt = self.doc_vectorizer is None
        index_is_corrupt = index_is_corrupt or (
            self.all_documents_sparse_vectors is None)
        index_is_corrupt = index_is_corrupt or (self.all_documents_ids is None)
        if index_is_corrupt:
            print("Index is corrupted, please rebuild index")

        time_elapsed = time.time()-start_time
        print(f"document index load_index ends after {time_elapsed} seconds")
        print("-"*30)

    def _create_index(self, documents):
        """Create a new index using provided documents

        Args:
            documents (list): list of documents from which the index will be built
        """
        start_time = time.time()

        print("creating index...")
        if self.index_type == "tf_idf_sklearn":
            doc_texts = []
            doc_ids = []
            for doc in documents:
                doc_texts.append(doc["text"])
                doc_ids.append(doc["id"])

            tokenizer_lemmatizer = LemmaTokenizer()
            doc_tf_idf_vectorizer = TfidfVectorizer(tokenizer=tokenizer_lemmatizer, ngram_range=(1, 2),
                                                    min_df=1, max_df=1.0)
            doc_term_tf_idf_weights = doc_tf_idf_vectorizer.fit_transform(
                doc_texts)  # sparse matrix of shape (nb_docs,nb_terms)

            # save tf_idf weights and vectorizer
            print("Saving index...")
            vectorizer_path = os.path.join(
                self.path_to_index_dir, "doc_tf_idf_vectorizer.joblib")
            weights_matrix_path = os.path.join(
                self.path_to_index_dir, "doc_term_tf_idf_weights.joblib")
            dump(doc_tf_idf_vectorizer, vectorizer_path)
            dump(doc_term_tf_idf_weights, weights_matrix_path)

            index_json = {"doc_tf_idf_vectorizer_path": vectorizer_path,
                          "doc_term_tf_idf_weights_path": weights_matrix_path,
                          "doc_db_ids": doc_ids
                          }

            with open(self.path_to_index_file, 'w') as outfile:
                json.dump(index_json, outfile)
                print("saving index at ", self.path_to_index_file)

        print("document index create_index ends after {} seconds".format(
            time.time()-start_time))
        print("-"*30)

        self._load_index()

    def query_similar_document_ids(self, query, nb_docs=1):
        """query documents ids similar to query

        Args:
            query (str): document from which similar documents will be computed
            nb_docs (int, optional): Max number of similar documents to return. Defaults to 1.

        Returns:
            tuple: similar documents ids and scores
        """
        # https://github.com/facebookresearch/DrQA/drqa/retriever/tfidf_doc_ranker.py
        # Above link is a way to manually query documents ids from index sparse matrix file
        if self.index_type == "tf_idf_sklearn":
            vectorized_query = self.doc_vectorizer.transform([query])
            # print(f"vectorized query here: {vectorized_query}, type {type(vectorized_query)}, shape : {vectorized_query.shape}")

            docs_query_similarities = self.all_documents_sparse_vectors.dot(
                vectorized_query.reshape(-1, 1)).toarray()[:, 0]

            most_similar_docs_positions = np.argsort(
                docs_query_similarities)[-nb_docs:]

            most_similar_docs_ids = np.array(self.all_documents_ids)[
                most_similar_docs_positions]
            most_similar_docs_scores = docs_query_similarities[most_similar_docs_positions]
            most_similar_docs_scores = dict(
                zip(most_similar_docs_ids, most_similar_docs_scores))

            return most_similar_docs_ids, most_similar_docs_scores

        return None
