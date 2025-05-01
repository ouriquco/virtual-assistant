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
Built-in SQL injection detection and prevention.
Built-in direct and indirect prompt injection detection and prevention

# 🛠️ Installation
```
git clone https://github.com/yourusername/flight-sql-assistant.git
cd virtual-assistant
pip install -r requirements.txt
```

# ⚡ Quick Start
Configure your database connection and set HOST, USER, PASSWORD and DATABASE as environment variables.
Set your AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET and OPENROUTER_API_KEY as environment variables.

## Run the assistant:
python app.py

