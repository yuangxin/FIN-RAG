import os
from langchain_openai import ChatOpenAI
from config import DEEPSEEK_API_KEY, LLM_MODEL, LLM_BASE_URL, LLM_TEMPERATURE

llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=DEEPSEEK_API_KEY,
    base_url=LLM_BASE_URL,
    temperature=LLM_TEMPERATURE,
    streaming=True,
)
