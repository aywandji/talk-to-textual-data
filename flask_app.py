import json

from flask import Flask, render_template, request

from odqapy import pipeline
from odqapy.reader import DocumentReader
from odqapy.retriever import DocumentRetriever
from setup_data import DB_FILE_PATH, DOCS_INDEX_DIR, QA_MODELS_DIR, NLTK_DATA_DIR, QA_MODEL_NAME

app = Flask(__name__)
doc_retriever = DocumentRetriever(DOCS_INDEX_DIR, DB_FILE_PATH, NLTK_DATA_DIR)
doc_reader = DocumentReader(model_name=QA_MODEL_NAME,
                            models_dir=QA_MODELS_DIR)


@app.route("/")
def index():
    """Set up web app entry page

    Returns:
        [Flask Template]: template of index.html
    """
    return render_template('index.html')

@app.route("/query", methods=["POST"])
def query():
    """Request and return answers from odqa pipeline

    Returns:
        Json: json string containing answers
    """
    data = request.json
    question = data['question']
    json_answer = {"answer": "Please ask a question.",
                   "url": "", "context": ""}
    if len(question) < 2:
        return json.dumps(json_answer)

    answers, documents = pipeline(
        question, doc_retriever, doc_reader, nb_answers=5)

    sorted_ans_docs = sorted(zip(answers, documents), #sort by doc score
                             key=lambda x: x[1]["score"], reverse=True)
    # best_answer = sorted_ans_docs[0][0]
    # best_doc = sorted_ans_docs[0][1]
    # json_answer["answer"] = best_answer["text"]
    # json_answer["context"] = best_doc["text"]
    # json_answer["url"] = best_doc["url"]

    list_json = []
    for answer,doc in sorted_ans_docs:
        json_answer = {"answer": "Please ask a question.",
                   "url": "", "context": ""}
        json_answer["answer"] = answer["text"]
        json_answer["context"] = doc["text"]
        json_answer["url"] = doc["url"]
        list_json.append(json_answer)

    return json.dumps(list_json)


if __name__ == "__main__":
    app.run(debug=True)
