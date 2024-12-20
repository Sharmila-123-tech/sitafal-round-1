# -*- coding: utf-8 -*-
"""Chat with Website Using RAG .ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1CNr5xluAM-nD0_ubQP0LxL99zKrbdp9j
"""

!pip install requests beautifulsoup4 faiss-cpu transformers langchain

import requests
from bs4 import BeautifulSoup
from transformers import BertTokenizer, BertModel
import torch
import faiss
import numpy as np

# Function to scrape and extract content from websites
def scrape_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract all text content from the website
    paragraphs = soup.find_all('p')
    text = ' '.join([p.get_text() for p in paragraphs])

    return text

# Function to split content into chunks
def split_into_chunks(text, chunk_size=512):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

# Load the pre-trained BERT model and tokenizer for embedding generation
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertModel.from_pretrained("bert-base-uncased")

# Function to convert text into embeddings using BERT
def text_to_embedding(text):
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).numpy()

# Function to create vector embeddings for chunks and store them in FAISS
def create_vector_database(urls):
    embeddings = []
    metadata = []

    for url in urls:
        text = scrape_website(url)
        chunks = split_into_chunks(text)

        for chunk in chunks:
            embedding = text_to_embedding(chunk)
            embeddings.append(embedding)
            metadata.append({'url': url, 'text': chunk})

    embeddings = np.vstack(embeddings)  # Convert list of embeddings to a numpy array

    # Create FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    return index, metadata

# Example URLs to scrape
urls = ["https://www.uchicago.edu/", "https://www.washington.edu/", "https://www.stanford.edu/", "https://und.edu/"]

# Create the vector database
index, metadata = create_vector_database(urls)

# Function to handle a user's query
def query_to_embedding(query):
    return text_to_embedding(query)

# Function to retrieve the most relevant chunks from FAISS
def retrieve_relevant_chunks(query_embedding, index, metadata, top_k=5):
    D, I = index.search(query_embedding, top_k)

    # Retrieve the corresponding chunks and metadata
    results = []
    for i in I[0]:
        results.append(metadata[i])

    return results

# Example query
query = "What is the University of Chicago known for?"

# Convert the query to embedding
query_embedding = query_to_embedding(query)

# Retrieve relevant chunks from the index
relevant_chunks = retrieve_relevant_chunks(query_embedding, index, metadata)
for result in relevant_chunks:
    print(f"URL: {result['url']}\nText: {result['text']}\n")

from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Load a pre-trained GPT model and tokenizer for response generation
gpt_tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
gpt_model = GPT2LMHeadModel.from_pretrained("gpt2")

# Set the padding token to the eos_token if not already set
gpt_tokenizer.pad_token = gpt_tokenizer.eos_token

# Function to generate response based on retrieved chunks
def generate_response(query, relevant_chunks):
    # Combine the query and retrieved chunks into a single prompt
    context = f"Question: {query}\n\nContext:\n"
    context += '\n'.join([chunk['text'] for chunk in relevant_chunks])

    # Tokenize the input
    inputs = gpt_tokenizer.encode(context, return_tensors="pt", truncation=True, padding=True, max_length=1024)

    # Generate response with max_new_tokens to avoid exceeding the input length
    outputs = gpt_model.generate(inputs, max_new_tokens=150, num_return_sequences=1)

    # Decode the output
    response = gpt_tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

# Example query for the University of Washington
query = "About washington university?"

# Example relevant chunks (ensure this is a list of dictionaries with 'text' field)
relevant_chunks = [{'text': ""}]

# Generate response for the example query
response = generate_response(query, relevant_chunks)
print("Generated Response:", response)