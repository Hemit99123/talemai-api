"""Helper module for querying LLM with context from AstraDB vector store."""

import os
import requests
from dotenv import load_dotenv
from langchain_astradb import AstraDBVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables
load_dotenv()

ASTRA_DB_API_ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
ASTRA_DB_APPLICATION_TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_NAMESPACE = os.getenv("ASTRA_DB_NAMESPACE")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def query_model(context, query):
    """Query the Groq LLM API with a given context and user query."""
    system_prompt = "Roleplay as a Q&A chatbot."

    prompt = (
        "Use the following context to answer the question. Think about the contents of the context "
        "carefully to formulate a specific and accurate answer based on the query given.\n"
        "If you don't know the answer, just say that you don't know.\n\n"
        f"Context: {context}\nQuery: {query}"
    )

    print(context)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result["choices"][0]["message"]["content"]


def fetch_and_query(query):
    """Fetch relevant context using vector search and send it along with the query to the LLM."""
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
    retrieved_docs = retriever.invoke(query)
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])

    print(context)

    try:
        return query_model(context, query)
    except requests.exceptions.RequestException as e:
        return f"Request error occurred: {str(e)}"
    except KeyError:
        return "Unexpected response format from LLM API."
    except ValueError as e:
        return f"Value error occurred: {str(e)}"
    except Exception as e:
        # TODO: Narrow this catch block to specific exception types if needed
        return f"An unexpected error occurred: {str(e)}"
