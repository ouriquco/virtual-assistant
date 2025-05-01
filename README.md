# ✈️ Flight Planner Assistant

A powerful AI assistant that answers questions about flights and air traffic data, generates safe SQL queries, and provides structured information extraction-all powered by LangChain and modern LLMs.

# 🚀 Features
## Flight Information Retrieval:
Ask about flight prices, schedules, itineraries, and more.

## Structured Data Extraction:
Extract flight parameters (origin, destination, date, passengers) from user queries using Pydantic models.

## SQL Query Generation:
Converts natural language questions into safe, executable SQL queries for your air traffic database.

## Contextual Prompting:
Uses advanced prompt engineering and retrieval-augmented generation for accurate, context-aware responses.

## Safety First:
- Built-in SQL injection detection and prevention.
- Built-in direct and indirect prompt injection detection and prevention

# 🛠️ Installation
```
git clone https://github.com/yourusername/flight-sql-assistant.git
cd virtual-assistant
pip install -r requirements.txt
```

# ⚡ Quick Start
Configure your database connection and get API keys. Then set:
- HOST
- USER
- PASSWORD
- DATABASE
- AMADEUS_CLIENT_ID
- AMADEUS_CLIENT_SECRET
- OPENROUTER_API_KEY
  
as environment variables

## Run the assistant:
```python app.py```

## Ask questions!

1. “What’s the cheapest flight from SFO to JFK on July 1, 2025?”

2. “Total air traffic in 2020?”

3. “Generate a SQL query for flights from LAX to HNL in June.”



