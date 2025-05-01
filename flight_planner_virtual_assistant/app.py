import gradio as gr
from langchain_community.cache import RedisCache
from langchain.globals import set_llm_cache
from redis import Redis
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import FewShotPromptTemplate
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from router import Router, ChatOpenRouter
from dotenv import load_dotenv
import torch
import argparse
import os 

def parse_args():
    parser = argparse.ArgumentParser(description="Flight Planner Virtual Assistant")
    parser.add_argument("--llm", type=str, default='deepseek', choices=['deepseek', 'moonshot', 'mistral'], help="LLM to use (choose from: %(choices)s)")
    return parser.parse_args()

def get_prompt_injection_scanner():
    tokenizer = AutoTokenizer.from_pretrained("ProtectAI/deberta-v3-base-prompt-injection-v2")
    model = AutoModelForSequenceClassification.from_pretrained("ProtectAI/deberta-v3-base-prompt-injection-v2")

    classifier = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    truncation=True,
    max_length=512,
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    )
    return classifier

def get_llm(model_name):
    if model_name == 'deepseek':
        return ChatOpenRouter(model_name="deepseek/deepseek-chat-v3-0324:free")
    elif model_name == 'moonshot':
        return ChatOpenRouter(model_name="moonshotai/moonlight-16b-a3b-instruct:free")
    elif model_name == 'mistral':
        return ChatOpenRouter(model_name="mistralai/mistral-7b-instruct:free")
    else:
        raise ValueError(f"Unsupported LLM: {model_name}")

def setup_router(llm, number_of_results):

    example_prompt = PromptTemplate.from_template("""
        You are an expert flight planner assistant.
        Use the following examples to answer the user's question:
                                                  
        Question: {question}
        Answer: {answer}
        """)
    
    examples = [
        {"question":"What is the cheapest flight from San Jose to Kona on July 15th 2025?",
         "answer":"flight api",},
        {"question":"What is the most expensive flight from Los Angelas to Las Vegas on May 19th 2025?",
         "answer":"flight api",},
         {"question":"What is the earliest flight from San Diego to Seattle on July 15th 2025?",
         "answer":"flight api",},
         {"question":"What is the total air traffic in 2020?",
         "answer":"database",},
         {"question":"What was the air traffic like for every month in 2024?",
         "answer":"database",},
         {"question":"What is the average air traffic in 2022?",
         "answer":"database",},
         {"question":"What is the weather like in Kona in July?",
         "answer":"general",},
         {"question":"What is the best time to visit Hawaii?",
         "answer":"general",},
         {"question":"What are the top 10 tourist attractions in Hawaii?",
         "answer":"general",},
        ]
    example_prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        suffix="Question: {input}",
        input_variables=["input"],
    )

    sql_prompt = (
        """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

        Question: {question}
        SQL Query: {query}
        SQL Result: {result}
        your response should be a concise answer to the question."""
        )

    web_prompt = ('''You are an expert flight planner assistant.
                    
    Given the following web search results:
    {context}
                  
    Tasks:
    - Answer the question below using the web search results.
    - If the web search results contain a list of items, summarize the list in your answer.
    - If the web search results do not contain enough information to answer the question, reply: "I don't know."
    ''')
       
    try: 
        new_router = Router(
            llm=llm,
            system_prompt=example_prompt,
            web_prompt=web_prompt,
            sql_prompt=sql_prompt,
            number_of_results=number_of_results,
        )
        return new_router
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def answer_question(user_input, router, prompt_scanner): 
    try:
        injection = prompt_scanner(user_input)[0]
        is_injection = injection['label']
        risk_score = injection['score']
       
        if is_injection == 'INJECTION':
            return f"⚠️ Prompt Injection Detected! Risk Score: {risk_score:.2f}. Please rephrase your question."
        return router.route(user_input)
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def main():
    load_dotenv()
    os.environ['USER'] = 'root'
    number_of_results = 5
    args = parse_args()
    llm = get_llm(args.llm)
    set_llm_cache(RedisCache(redis_=Redis(host="localhost", port=6379)))
    router = setup_router(llm, number_of_results)
    prompt_scanner = get_prompt_injection_scanner()

    with gr.Blocks(title="Flight Planner Virtual Assistant") as demo:
        gr.Markdown("## 📚 Flight Planner Virtual Assistant")
        gr.Markdown("Ask me questions about flight details, air traffic, or general information.")

        with gr.Row():
            user_input = gr.Textbox(placeholder="Ask something like 'What is the cheapest airfare from San Jose to Kona on June 1st 2025?'", label="Your Question")

        output = gr.Textbox(label="Virtual Assistant Answer", lines=10)
        user_input.submit(fn=lambda x: answer_question(x, router, prompt_scanner), inputs=[user_input], outputs=output)
    
    demo.launch(share=True)

if __name__ == "__main__":
    main()