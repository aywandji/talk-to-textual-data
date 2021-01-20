import os
import glob
import shutil

from transformers import AutoTokenizer
from transformers import TFAutoModelForQuestionAnswering
import tensorflow as tf

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # deactivate GPU

# def download_qa_model(model_dir_path, model_name):
#     print("Downloading model...")
#     cache_dir = os.path.join(model_dir_path, "cache_dir")
#     tokenizer = AutoTokenizer.from_pretrained(
#         self.model_name, cache_dir=cache_dir)
#     model = TFAutoModelForQuestionAnswering.from_pretrained(
#         self.model_name, cache_dir=cache_dir)
#     # Save model and remove cache
#     print("Saving model...")
#     shutil.rmtree(cache_dir)
#     self.model.save_pretrained(model_dir_path)
#     self.tokenizer.save_pretrained(model_dir_path)

class DocumentReader:
    # TODO
    # - retrieve string answers for all contexts (in read_answer) using parallel computing

    def __init__(self, model_name="distilbert-base-uncased-distilled-squad",
                 models_dir="qa_models/"):
        """initialise doc reader instance and load model used for reading documents

        Args:
            model_name (str, optional): Name of huggingface model to load. 
                Defaults to "distilbert-base-uncased-distilled-squad".
            models_dir (str, optional): path to the directory where all models are saved. 
                Defaults to "qa_models/".
        """
        self.model_name = model_name
        self._models_dir = models_dir
        self.model_path = os.path.join(
            self._models_dir, model_name.replace("-", "_"))
        self._load_model()

    def _load_model(self):
        """Load model located at self.model_path. 
        If it doesn't exist, download the model and save it.
        """
        if not os.path.isdir(self._models_dir):
            os.mkdir(self._models_dir)

        if not os.path.isdir(self.model_path):
            os.mkdir(self.model_path)

        if len(glob.glob(self.model_path+"/*.h5")) == 0:
            # Download model
            print("Downloading model...")
            cache_dir = os.path.join(self.model_path, "cache_dir")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, cache_dir=cache_dir)
            self.model = TFAutoModelForQuestionAnswering.from_pretrained(
                self.model_name, cache_dir=cache_dir)
            # Save model and remove cache
            print("Saving model...")
            shutil.rmtree(cache_dir)
            self.model.save_pretrained(self.model_path)
            self.tokenizer.save_pretrained(self.model_path)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = TFAutoModelForQuestionAnswering.from_pretrained(
                self.model_path)

    def read_answer(self, question, contexts):
        """Read and return answers of question using provided contexts. One answer per context

        Args:
            question (str): raw question
            contexts (list): list of contexts fromo which different answers will be returned

        Returns:
            list:  list of answers retrieved from all contexts
        """
        nb_answers = len(contexts)
        question_duplicates = [question] * nb_answers
        tokenized_qc_pair = self.tokenizer(question_duplicates, contexts, padding=True,
                                           return_token_type_ids=True, return_tensors="tf")

        qa_outputs = self.model(tokenized_qc_pair)
        answers_start_index = tf.argmax(qa_outputs[0], axis=1)
        answers_end_index = tf.argmax(qa_outputs[1], axis=1)

        answers_start_proba_scores = tf.nn.softmax(qa_outputs[0])
        answers_end_proba_scores = tf.nn.softmax(qa_outputs[1])

        answers = []
        for i in range(nb_answers):
            start_index = answers_start_index[i]
            end_index = answers_end_index[i]
            answer_tokens_ids = tokenized_qc_pair["input_ids"][i,
                                                               start_index:end_index+1]
            answer_tokens = self.tokenizer.convert_ids_to_tokens(
                answer_tokens_ids.numpy())
            string_answer = self.tokenizer.convert_tokens_to_string(
                answer_tokens)

            answers.append({"text": string_answer,
                            "start_score": qa_outputs[0][i, start_index].numpy(),
                            "end_score": qa_outputs[1][i, end_index].numpy(),
                            "start_proba": answers_start_proba_scores[i, start_index].numpy(),
                            "end_proba": answers_end_proba_scores[i, end_index].numpy()})

        return answers
