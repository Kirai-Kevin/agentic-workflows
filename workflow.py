import os
from dotenv import load_dotenv
from typing import TypedDict
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from database_setup import query_db, DB_DESCRIPTION

# Load environment variables
load_dotenv()

# Get API keys from environment variables
LLAMA_API = os.getenv("LLAMA_API_KEY")
LANGSMITH_API = os.getenv("LANGSMITH_API_KEY")

# Ensure the API keys are set
if not LLAMA_API:
    print("LLAMA_API_KEY not found in .env file")
if not LANGSMITH_API:
    print("LANGSMITH_API_KEY not found in .env file")

if not LLAMA_API or not LANGSMITH_API:
    raise ValueError("API keys not set. Please check your .env file.")

# Configure LangSmith (optional, for tracking)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API
os.environ["LANGCHAIN_PROJECT"] = "RetailX_AI_Assistant"

# Initialize the model
model = ChatOpenAI(
    api_key=LLAMA_API,
    base_url="https://api.llama-api.com",
    model="llama3-70b"
)

# Define prompts
can_answer_prompt = PromptTemplate(
    template="""Given the following database description and user question, determine if the question can be answered using the available data. Return a JSON with 'reasoning' and 'can_answer' keys.

Database Description:
{db_description}

User Question: {question}

JSON Response:""",
    input_variables=["db_description", "question"],
)

write_query_prompt = PromptTemplate(
    template="""Given the following database description and user question, write an SQL query to answer the question.

Database Description:
{db_description}

User Question: {question}

SQL Query:""",
    input_variables=["db_description", "question"],
)

write_answer_prompt = PromptTemplate(
    template="""Given the user question, SQL query, and query result, provide a human-readable answer.

User Question: {question}
SQL Query: {query}
Query Result:
{result}

Answer:""",
    input_variables=["question", "query", "result"],
)

# Define workflow functions
def check_if_can_answer(state):
    result = model.invoke(can_answer_prompt.format(db_description=DB_DESCRIPTION, question=state["question"]))
    parsed = JsonOutputParser().parse(result["choices"][0]["message"]["content"])
    return {"plan": parsed["reasoning"], "can_answer": parsed["can_answer"]}

def write_query(state):
    result = model.invoke(write_query_prompt.format(db_description=DB_DESCRIPTION, question=state["question"]))
    return {"sql_query": result["choices"][0]["message"]["content"]}

def execute_query(state):
    query = state["sql_query"]
    try:
        return {"sql_result": query_db(query).to_markdown()}
    except Exception as e:
        return {"sql_result": str(e)}

def write_answer(state):
    result = model.invoke(write_answer_prompt.format(
        question=state["question"],
        query=state["sql_query"],
        result=state["sql_result"]
    ))
    return {"answer": result["choices"][0]["message"]["content"]}

# Define workflow state
class WorkflowState(TypedDict):
    question: str
    plan: str
    can_answer: bool
    sql_query: str
    sql_result: str
    answer: str

# Create and configure the workflow
workflow = StateGraph(WorkflowState)

workflow.add_node("check_if_can_answer", check_if_can_answer)
workflow.add_node("write_query", write_query)
workflow.add_node("execute_query", execute_query)
workflow.add_node("write_answer", write_answer)

workflow.set_entry_point("check_if_can_answer")

workflow.add_conditional_edges(
    "check_if_can_answer",
    lambda x: "write_query" if x["can_answer"] else END,
)

workflow.add_edge("write_query", "execute_query")
workflow.add_edge("execute_query", "write_answer")
workflow.add_edge("write_answer", END)

# Compile the workflow
app = workflow.compile()

def process_question(question: str) -> str:
    try:
        result = app.invoke({"question": question})
        return result.get("answer", "Sorry, I couldn't answer that question based on the available data.")
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Make sure process_question is available for import
__all__ = ['process_question']
