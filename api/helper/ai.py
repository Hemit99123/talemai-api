"""Helper module for querying the Cohere LLM API."""

from os import getenv
import cohere

COHERE_API_KEY = getenv("COHERE_API_KEY")


async def query_model(context, query):
    """Query the Cohere LLM API with a given context and user query."""

    co = cohere.ClientV2(COHERE_API_KEY)

    system_prompt = (
        "You are a RAG chatbot. Use the documents given to properly answer the query.\n"
        "If you do not understand the question, ask for clarity with insight-seeking questions.\n"
        "If you don't know the answer, just say that you don't know.\n"
        "Do not make up any information, and do not hallucinate.\n"
        "Do not repeat the question verbatim in your answer.\n"
        "Do not mention that you are getting information from a text. Talk naturally."
    )

    response = co.chat(
        model="command-r-plus-08-2024",
        messages=[
            {"role": "user", "content": query},
            {"role": "system", "content": system_prompt}
        ],
        documents=[context]
    )

    return response.message.content[0].text
