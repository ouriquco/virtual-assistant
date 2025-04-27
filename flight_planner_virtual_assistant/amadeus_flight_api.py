import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv
from pydantic import BaseModel, Field
load_dotenv()

class FlightParams(BaseModel):
    origin: str = Field(description="Departure city/IATA code")
    destination: str = Field(description="Arrival city/IATA code")
    departure_date: str = Field(description="Date in YYYY-MM-DD format")
    adults: int = Field(1, description="Number of adult passengers")

class AmadeusAPI:
    def __init__(self, client_id, client_secret):
        self.client = Client(client_id=client_id, client_secret=client_secret)

    def find_flights(self, origin, destination, departure_date, currency='USD', adults=1, max_price=None):
        try:
            params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': adults,
                'currencyCode': currency,
            }
            if max_price:
                params['maxPrice'] = max_price

            response = self.client.shopping.flight_offers_search.get(**params)
            return response.data
        except ResponseError as error:
            print(error)
    
    def print_flight_offers(self, flight_offers):
        if not os.path.exists('./flight_data'):
            os.makedirs('./flight_data')
      
        with open('./flight_data/flight_offers.txt', 'w') as file:
            for offer in flight_offers:
                file.write(f"Price: {offer['price']['total']} {offer['price']['currency']}")
                print(f"Price: {offer['price']['total']} {offer['price']['currency']}")
                for itinerary in offer['itineraries']:
                    file.write(f"  Itinerary duration: {itinerary['duration']}\n")
                    print(f"  Itinerary duration: {itinerary['duration']}")
                    for segment in itinerary['segments']:
                        file.write(f"    {segment['departure']['iataCode']} -> {segment['arrival']['iataCode']} "
                                f"on {segment['departure']['at']}\n")
                        print(f"    {segment['departure']['iataCode']} -> {segment['arrival']['iataCode']} "
                            f"on {segment['departure']['at']}")
                file.write('-' * 40 + '\n')
                print('-' * 40)
            