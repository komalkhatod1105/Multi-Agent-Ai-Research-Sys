from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search , scrape_url 
from dotenv import load_dotenv
import os

load_dotenv()

def get_llm():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your environment to run research."
        )
    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        api_key=api_key,
    )


#1st agent 
def build_search_agent():
    return create_agent(
        model = get_llm(),
        tools= [web_search]
    )

#2nd agent 

def build_reader_agent():
    return create_agent(
        model = get_llm(),
        tools = [scrape_url]
    )


writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. Write clear, structured and insightful reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points)
- Conclusion
- Sources (list all URLs found in the research)

Be detailed, factual and professional."""),
])

critic_prompt = ChatPromptTemplate.from_messages([
     ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

class LazyChain:
    def __init__(self, prompt):
        self.prompt = prompt

    def invoke(self, inputs):
        return (self.prompt | get_llm() | StrOutputParser()).invoke(inputs)


writer_chain = LazyChain(writer_prompt)
critic_chain = LazyChain(critic_prompt)
