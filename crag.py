import os
from dotenv import load_dotenv
from typing import List, Optional

# import chromadb
# from chromadb.utils import embedding_functions

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from deepagents import create_deep_agent

from faq_documents import FAQ_DOCUMENTS

# Load environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set.")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = Chroma(
    collection_name="hr_faqs",
    embedding_function=embeddings,
)

if len(vectorstore.get()["ids"]) == 0:
    texts = [f"Q: {faq['question']}\nA: {faq['answer']}" for faq in FAQ_DOCUMENTS]
    metadatas = [{"question": faq["question"], "answer": faq["answer"]} for faq in FAQ_DOCUMENTS]
    vectorstore.add_texts(texts=texts, metadatas=metadatas)
    print(f"Ingested {len(FAQ_DOCUMENTS)} FAQ documents.")

@tool
def query_knowledge_base(query: str) -> str:
    """
    Search the company HR/IT knowledge base for documents related to a query.
    Returns the top relevant FAQ text.
    """
    docs = vectorstore.similarity_search(query, k=3)
    if not docs:
        return "No relevant documents found."
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


SYSTEM_PROMPT = """You are an HR and IT support assistant for the company.
You MUST answer ONLY from the provided internal documents.
To answer a user question, follow these steps carefully:

1. Call the tool `query_knowledge_base` with the user's exact question to get relevant documents.
2. Examine the returned documents. If they contain enough information to answer, do so.
3. If the documents are irrelevant or insufficient:
   a. Think of a better, more specific search phrase.
   b. Call `query_knowledge_base` again with the improved query.
   c. Repeat if needed, but after two attempts if still not found, tell the user that
      the information is not available and ask them to rephrase.
4. Always answer concisely and professionally, citing only the documents.

Never invent information. If you cannot find the answer, say so clearly."""


agent = create_deep_agent(
    model=ChatOpenAI(model="gpt-5-nano", temperature=0.2),
    tools=[query_knowledge_base],
    system_prompt=SYSTEM_PROMPT,
)

print("HR Chatbot with DeepAgents (CRAG logic) ready. Type 'exit' to quit.\n")
messages = []

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ("exit", "quit"):
        break
    if not user_input:
        continue

    messages.append(HumanMessage(content=user_input))

    # Run the agent – it will call tools autonomously and follow the CRAG steps.
    result = agent.invoke({"messages": messages})

    # The agent returns a list of messages; the last AI message is the reply.
    final_answer = result["messages"][-1].content
    print(f"Bot: {final_answer}\n")

    # Keep the full conversation history for the next turn
    messages = result["messages"]