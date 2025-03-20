from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import time

app = FastAPI()

LLAMA2_URL = "http://ollama-container:11434/api/generate"

class QueryRequest(BaseModel):
    question: str

def scrape_website(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return " ".join([p.get_text() for p in soup.find_all("p")])[:2000] #truncate web response
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return None

def query_ai(context):
    payload = {"model": "llama2",
               "prompt": f"Summarize this: {context}",
               "stream": False}
    response = requests.post(LLAMA2_URL, json=payload)
    return response.json().get("response", "NOT_ENOUGH_INFO")

@app.post("/ask")
def ask_question(query: QueryRequest):
    search_results = list(search(query.question, num_results=2)) #limit for testing
    for url in search_results:
        content = scrape_website(url)
        if content:
            ai_response = query_ai(content)
            if "NOT_ENOUGH_INFO" not in ai_response.strip():
                return {"answer": ai_response, "source": url}
        time.sleep(2)  # To avoid getting blocked
    
    return {"answer": "I cannot confidently answer this question.", "source": None}
