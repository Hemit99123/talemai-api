import json
import requests

async def query_model(context, query):
    """Query the Groq LLM API with a given context and user query."""
    system_prompt = "Roleplay as a Q&A chatbot."

    # Prompt engineering to ensure the model understands the task
    prompt = (
        f"Context: {context}\nQuery: {query}\n\n"
        "Use the above context to answer the query. Think about the contents of the context deeply and meaningfully. Truly analyze the query and context surrounding it\n"
        "If you don't know the answer, just say that you don't know.\n"
        "Do not make up any information, and do not hallucinate.\n"
        "Do not say 'Based on the provided context', or similar phrases.\n"  
        "Do not repeat the question in your answer.\n"
    )

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

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return "The request timed out. Please try again later."
    except requests.exceptions.RequestException as e:
        return f"Request error occurred: {str(e)}"
    except json.JSONDecodeError:
        return "Failed to parse response from LLM API."
    except (KeyError, IndexError):
        return "Unexpected response format from LLM API."