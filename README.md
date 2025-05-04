<!-- markdownlint-disable first-line-h1 -->
<!-- markdownlint-disable html -->
<!-- markdownlint-disable no-duplicate-header -->

<div align="center">
  <img src="https://i.ibb.co/ns0wZdtj/I-20250310-004605-0000-1-removebg-preview.png/" width="30%" alt="Talem AI" />
</div>
<hr>
<div align="center" style="line-height: 1;">
  <a href="https://talem.org/ai"><img alt="Demo"
    src="https://img.shields.io/badge/🚀%20Live%20Demo-Talem%20AI-2F80ED?color=2F80ED&logoColor=white"/></a>
  <a href="https://huggingface.co/microsoft/Phi-3.5-mini-instruct"><img alt="Model Hub"
    src="https://img.shields.io/badge/🧠%20Model%20Hub-Talem%20AI-8E44AD?color=8E44AD&logoColor=white"/></a>
  <br>
  <a href="https://twitter.com/talem_ai"><img alt="Twitter"
    src="https://img.shields.io/badge/Twitter-@talem__ai-1DA1F2?logo=x&logoColor=white"/></a>
  <br>
  <a href="LICENSE-CODE"><img alt="Code License"
    src="https://img.shields.io/badge/Code%20License-Apache%202.0-00BFFF?color=00BFFF"/></a>
  <br>
</div>

## Table of Contents

1. [Introduction](#1-introduction)  
2. [Key Technologies](#2-key-technologies)  
3. [Developer Credits](#3-developer-credits)  
4. [Demo](#4-demo)

## 1. Introduction

Talem AI is a RAG application. This codebase holds the code for the REST API mircoservice hosting the backend functions. It's main purpose is to act like a Q&A chatbot who provides answers to prompts about different college programs. To gain specialized context within this domain, we vectorize college information brochours and through **Langchain**, this information is retrieved based on it's similarity to the user's prompt and given as **context** to the prompt into Groq REST API.

## 2. Key Technologies

### Python 🐍
Python is the programming language of choice for this project
<br>
#### LangChain 👨‍🔬
Langchain abstracts a lot of the RAG logic, allowing for faster development times. 
<br>
#### AstraDB 💽
AstraDB allows for the storage of the vector embeddings (context) which are retrieved by the different materials we want our LLM to be well-versed in.
<br>
#### Groq REST API
Groq allows us to access hosted LLMs which will feed on these vector embeddings (context) and a well written prompt which is designed to be very speific and scientific to produce the best result.
<br>
#### sentence-transformers model
The vector embeddings are numbers which were produced through a complex algorithm. To convert them back into human readable syntax (needed to pass into LLM), we use this AI model provided by LangChain and HuggingFace.
<br>
#### FastAPI 💻
FastAPI allows us to build the REST API which will allow the frontend interface to request information through their query. Development times are fast and it was easy to set up. Response times are also fast.
<br>
