#!/usr/bin/env python3
"""
Test script for OpenAI client initialization.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Print client info to verify initialization
print(f"OpenAI client initialized successfully: {client}")
print(f"OpenAI client type: {type(client)}")

# Test a simple API call
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello!"}
    ],
    max_tokens=10
)

# Print response to verify API call
print(f"Response: {response.choices[0].message.content}")
