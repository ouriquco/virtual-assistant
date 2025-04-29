from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
import re
import os

class DB_QA:
    def __init__(self, host, user, password, database, template, llm):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.sql_prompt = template
        self.llm = llm

    def connect(self):
        try:
            self.connection = SQLDatabase.from_uri(f"mysql+mysqlconnector://{os.environ.get('USER')}:{os.environ.get('PASSWORD')}@{os.environ.get('HOST')}/{os.environ.get('DATABASE')}")
            print("Connection successful")
        except Exception as e:
            print(f"Error: {e}")

    def get_table_info(self):
        try:
            return self.connection.get_context()['table_info']
        except Exception as e:
            print(f"Error: {e}")

    def _is_safe_sql(self, query: str) -> bool:
        forbidden = {'delete', 'drop', 'update', 'insert', 'alter', 'truncate', 'create'}
        pattern = re.compile(r"\b(" + "|".join(forbidden) + r")\b", re.IGNORECASE)
        return not pattern.search(query.lower())

    def answer_query(self, query):
        try:

            execute_query = QuerySQLDataBaseTool(db=self.connection)
            query_template = PromptTemplate.from_template(
                "You are a professional MySQL expert. Given the following table information, generate a MySQL query to answer the user's question.\n"
                "Table Info: \n"
                "{table_info}\n\n"
                "Question: {question}\n"
                "Return just the SQL query, do not explain it.\n"
                "Make sure it's in the proper format.\n"
                "Example: SELECT SUM(`U.S. Airline Traffic - Domestic`) FROM `U.S. Air Traffic` WHERE `Date` LIKE '2020%';\n"
                ).partial(
                    table_info=self.get_table_info()
                )
            
            write_query = query_template | self.llm 
            print(write_query.invoke({"question":query}).content)
        
            sql_query = write_query.invoke({"question":query}).content
            if not self._is_safe_sql(sql_query):
                return "⚠️ SQL Injection Detected! Please rephrase your question."
            
            result = execute_query.invoke({"query":sql_query})
            
            sql_prompt = PromptTemplate.from_template(template=self.sql_prompt
            ).partial(
                query=sql_query,
                result=result
            )

            final_chain = sql_prompt | self.llm 
            return final_chain.invoke({"question":query}).content
        except Exception as e:
            print(f"Error in answer query function: {e}")