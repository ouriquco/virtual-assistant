from amadeus_flight_api import AmadeusAPI, FlightParams
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain 
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from web_scraper import run_web_scraper
from vectorstore import add_flights_to_vectorstore, get_vectorstore, add_web_search_to_vectorstore
from langchain_db import DB_QA
import time
import os
class ChatOpenRouter(ChatOpenAI):
    openai_api_base: str
    openai_api_key: str
    model_name: str

    def __init__(self,
                 model_name: str,
                 openai_api_base: str = "https://openrouter.ai/api/v1",
                 **kwargs):
        openai_api_key = os.getenv('OPENROUTER_API_KEY')
        super().__init__(openai_api_base=openai_api_base,
                         openai_api_key=openai_api_key,
                         model_name=model_name, **kwargs)

class Router:
    def __init__(self, llm, system_prompt, web_prompt, sql_prompt, number_of_results=5):
        self.number_of_results = number_of_results
        self.flight_parser = PydanticOutputParser(pydantic_object=FlightParams)
        self.llm = llm
        self.amadeus = AmadeusAPI(os.environ.get('AMADEUS_CLIENT_ID'), os.environ.get('AMADEUS_CLIENT_SECRET'))
        self.db = DB_QA(os.environ.get('HOST'),os.environ.get('USER'), os.environ.get('PASSWORD'), os.environ.get('DATABASE'), sql_prompt, llm)
        self.system_prompt = system_prompt
        self.web_prompt = web_prompt

    def route(self, query):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{input}"),
            ]
        )
        routing_result = self.llm.invoke(prompt.invoke({query})).content.lower()

        if routing_result == "flight api":
            return self.get_flight_information(query)
        elif routing_result == "general":
            return self.get_general_information(query)
        elif routing_result == "database":
            return self.get_database_information(query)
        else:
            return self.get_general_information(query)
            # raise ValueError("Invalid routing result")

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
            
            if not flights:
                print("There are no flight offers given. Starting web search.")
                return self.get_general_information(query)
            
            self.amadeus.print_flight_offers(flights)
            with open('./flight_data/flight_offers.txt', 'r') as f:
                data = f.read()

            offers = [offer.strip() for offer in data.split('-' * 40) if offer.strip()]
            vectorstore = get_vectorstore(collection_name="flight_data")
            add_flights_to_vectorstore(vectorstore, offers)
            
            flight_offer = '''
            Price: 1032.28 USD
            Itinerary duration: PT12H58M
            SJC -> PDX on 2025-06-01T09:23:00
            PDX -> SFO on 2025-06-01T13:35:00
            SFO -> KOA on 2025-06-01T16:55:00
            '''

            prompt = ('''
            You are a helpful assistant. Use ONLY the flight information below to answer the question. 

            ==== FLIGHT INFORMATION START ====
            {context}
            ==== FLIGHT INFORMATION END ====
            
            Question: {input}
                 
            Answer Format:
            - If the answer is present in the flight information, provide an answer in this format: {flight_offer}. 
            - If the answer is not present in the flight information, say "There are no flights based on the information given."
            ''')

            final_prompt = ChatPromptTemplate.from_messages([
                ("system", prompt),
                ("human", "{input}"),
            ]).partial(flight_offer=flight_offer)

            vectorstore = get_vectorstore("flight_data")
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            question_answer_chain = create_stuff_documents_chain(self.llm, final_prompt)
            chain = create_retrieval_chain(retriever, question_answer_chain)

             # Measure the time taken for the chain to run to test Redis cache
            start_time = time.perf_counter()
            response = chain.invoke({"input": query})
            end_time = time.perf_counter()
            print(f"Model Inference Time: {end_time - start_time:.2f} seconds")
            return response.get('answer')
        
        except Exception as e:
            print(f"Error: {e}")
            print("Please check the flight details and try again.")

    def get_general_information(self, query):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.web_prompt),
                ("human", "{input}"),
            ]
        )

        documents = run_web_scraper(query, self.number_of_results)
        vectorstore = get_vectorstore("web_data")
        add_web_search_to_vectorstore(vectorstore, documents)

        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        chain = create_retrieval_chain(retriever, question_answer_chain)

        # Measure the time taken for the chain to run to test Redis cache
        start_time = time.perf_counter()
        response = chain.invoke({"input": query})
        end_time = time.perf_counter()
        print(f"Model Inference Time: {end_time - start_time:.2f} seconds")
        return response.get('answer')

    def get_database_information(self, query):
        self.db.connect()
        return self.db.answer_query(query)
        


    
    