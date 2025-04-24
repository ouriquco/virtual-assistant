from amadeus_flight_api import AmadeusAPI, FlightParams
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from web_scraper import run_web_scraper
from vectorstore import run_vectorstore
from langchain_db import DB_QA
import os

class Router:
    def __init__(self, llm, system_prompt, prompt_template, sql_template, number_of_results=5):
        self.number_of_results = number_of_results
        self.flight_parser = PydanticOutputParser(pydantic_object=FlightParams)
        self.llm = llm
        self.amadeus = AmadeusAPI(os.environ.get('AMADEUS_CLIENT_ID'), os.environ.get('AMADEUS_CLIENT_SECRET'))
        self.db = DB_QA(os.environ.get('HOST'),os.environ.get('USER'), os.environ.get('PASSWORD'), os.environ.get('DATABASE'), sql_template, llm)
        self.system_prompt = system_prompt
        self.prompt_template = prompt_template

    def route(self, query):
        routing_result = self.llm.invoke(self.prompt_template.invoke({query})).content.lower()

        if routing_result == "flight api":
            return self.get_flight_information(query)
        elif routing_result == "general":
            return self.get_general_information(query)
        elif routing_result == "database":
            return self.get_database_information(query)
        else:
            raise ValueError("Invalid routing result")

    def get_flight_information(self, query):
        flight_prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract flight details from this query. {format_instructions}"""),
            ("human", "{input}")
        ]).partial(format_instructions=self.flight_parser.get_format_instructions())
        
        extraction_chain = flight_prompt | self.llm | self.flight_parser
        
        try:
            params = extraction_chain.invoke({"input": query})
            print(f'Check flight parameters {params}')
            flights = self.amadeus.find_flights(
                origin=params.origin,
                destination=params.destination,
                departure_date=params.departure_date,
                adults=params.adults
            )
            
            self.amadeus.print_flight_offers(flights)
        except Exception as e:
            print(f"Error: {e}")
            print("Please check the flight details and try again.")

    def get_general_information(self, query):
        run_web_scraper(query, self.number_of_results)
        run_vectorstore()

    def get_database_information(self, query):
        self.db.connect()
        return self.db.answer_query(query)
        


    
    