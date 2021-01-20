import time
import json
import sqlite3


class DataBaseClient:
    def __init__(self, db_file_path):
        """Create and instance and check that the database exists

        Args:
            db_file_path (str): path to the database file
        """
        start_time = time.time()
        self.db_file_path = db_file_path
        self._verify_database()  # check if database exists. If not, create it.
        print("Database initialisation  ends after {} seconds".format(
            time.time()-start_time))
        print("-"*30)

    def _documents_generator(self, docs_files_paths):
        """Generator of documents  as tuples for database SQL insertion

        Args:
            docs_files_paths (list): list of json files containing documents to generate

        Yields:
            tuple: tuple of fields to insert inside database
        """
        for doc_path in docs_files_paths:
            with open(doc_path) as doc_file:
                # dict with keys == (title,text,url)
                document_dict = json.load(doc_file)

                yield (document_dict["title"], document_dict["text"], document_dict["url"])

    def add_documents(self, docs_files_paths):
        """Add documents to the database

        Args:
            docs_files_paths (list ): list of documents to add
        """
        db_connection = self._create_connection()
        if db_connection is None:
            print("A connection couldn't be establish with database ",
                  self.db_file_path)
        else:
            try:
                cursor = db_connection.cursor()
                query = '''INSERT INTO documents(title,text,url) VALUES (?,?,?)'''
                cursor.executemany(
                    query, self._documents_generator(docs_files_paths))

                db_connection.commit()
            except sqlite3.Error as error:
                print("Error: ", error)

            db_connection.close()

    def _create_connection(self):
        """Create a new connection to the database

        Returns:
            object: connection object to query the database
        """
        db_connection = None
        try:
            db_connection = sqlite3.connect(self.db_file_path)
        except sqlite3.Error as error:
            print("Error: ", error)
        # finally:
        return db_connection

    def _create_table(self, db_connection, sql_command):
        """Create a new table inside the database

        Args:
            db_connection (object): database connection object
            sql_command (str): SQL command to execute
        """
        try:
            c = db_connection.cursor()
            c.execute(sql_command)

            db_connection.commit()
        except sqlite3.Error as e:
            print("Error: ", e)

    def _dict_factory(self, cursor, row):
        """method to parse each row returned by a database query

        Args:
            cursor (object): Cursor used to query the database
            row (object): returned row 

        Returns:
            dict: dictionary representing the returned row
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_documents(self, docs_ids=None):
        """Retrive documents from the database

        Args:
            docs_ids (list, optional): List of documents ids to return. 
            When None, all documents are returned. Defaults to None.

        Returns:
            list: list of documents
        """
        start_time = time.time()

        db_connection = self._create_connection()
        fields_to_fetch = ["id", "title", "text", "url"]
        query = '''SELECT {} FROM documents'''.format(
            ",".join(fields_to_fetch))

        if db_connection is None:
            print("A connection couldn't be establish with database ",
                  self.db_file_path)
            docs = []

        elif docs_ids is None:  # return all documents (as a generator):
            # query = '''SELECT * FROM documents'''
            db_connection.row_factory = self._dict_factory  # return rows parse are dictionary
            cursor = db_connection.cursor()
            cursor.execute(query)
            docs = cursor.fetchall()

        else:
            docs_ids = [str(i) for i in docs_ids]
            placeholder = "?"
            placeholders = ', '.join(placeholder for d_id in docs_ids)
            # query = '''SELECT id,text FROM documents WHERE id IN (%s)''' % placeholders
            query = query + " WHERE id IN (%s)" % placeholders

            db_connection.row_factory = self._dict_factory
            cursor = db_connection.cursor()
            cursor.execute(query, docs_ids)
            docs = cursor.fetchall()

        print("db client get_documents ends after {} seconds".format(
            time.time()-start_time))
        print("-"*30)

        return docs

    def _verify_database(self):
        """verify that a database with necessary tables exists. If not, create one. 
        """
        db_connection = self._create_connection()
        if db_connection is None:
            print("A connection couldn't be establish with database ",
                  self.db_file_path)
        else:
            create_documents_table_command = '''CREATE TABLE IF NOT EXISTS documents (
                                                id integer PRIMARY KEY,
                                                title text NOT NULL, 
                                                text text NOT NULL,
                                                url text NOT NULL
                                                ) 
                                             '''
            self._create_table(db_connection,
                               create_documents_table_command)
            db_connection.close()
