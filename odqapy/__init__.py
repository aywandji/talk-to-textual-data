# def pipeline(question=""):
#     if len(question) == 0:
#         return "Please ask a question."
#     return {"answer" : question}

def pipeline(question, doc_retriever, doc_reader, nb_answers=1):
    documents = doc_retriever.query_related_documents(
        question, nb_docs=nb_answers)
    contexts = [doc["text"] for doc in documents]
    answers = doc_reader.read_answer(question, contexts)

    return answers, documents