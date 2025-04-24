from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_core.prompts import PromptTemplate
import os

class DB_QA:
    def __init__(self, host, user, password, database, template, llm):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.sql_prompt = PromptTemplate.from_template(template=template)
        self.llm = llm

    def connect(self):
        try:
            self.connection = SQLDatabase.from_uri(f"mysql+mysqlconnector://{os.environ.get('USER')}:{os.environ.get('PASSWORD')}@{os.environ.get('HOST')}/{os.environ.get('DATABASE')}")
            print("Connection successful")
        except Exception as e:
            print(f"Error: {e}")

    def get_table_info(self):
        try:
            return self.connection.get_table_info()
        except Exception as e:
            print(f"Error: {e}")

    def answer_query(self, query):
        try:
            table_info = self.get_table_info()
            db_chain = create_sql_query_chain(
                llm=self.llm,
                db=self.connection,
                prompt=self.sql_prompt
            )
            return db_chain.invoke({"question": query, "dialect": None, "table_info": table_info, "top_k": 5})
        except Exception as e:
            print(f"Error: {e}")