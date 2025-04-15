from langchain_astradb import AstraDBVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_NAMESPACE = os.getenv("ASTRA_DB_NAMESPACE")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")



def query_model(context, query):
    # Prompt engineering to ensure LLM fits our use case correctly

    systemPrompt = "Roleplay as a Q&A chatbot."

    prompt = f"""Use the following context to answer the question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context: {context}
Question: {query}
"""


    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": systemPrompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    print(prompt)

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result["choices"][0]["message"]["content"]

def fetch_and_query(query):
    embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

    vectorstore = AstraDBVectorStore(
        collection_name="main_v2",
        embedding=embeddings,
        api_endpoint=ASTRA_DB_API_ENDPOINT,
        token=ASTRA_DB_APPLICATION_TOKEN,
        namespace=ASTRA_DB_NAMESPACE,
    )

    retriever = vectorstore.as_retriever()

    # Retrieve relevant context from stored embeddings
    retrieved_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    print(context)
    try:
        result = query_model(context, query)
        return result
    except Exception as e:
        return f"An error occurred: {str(e)}"
    