from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

response = client.chat.completions.create(model="llama3.1:8b", messages=[
    {"role": "system", "content": "You are a Linux SRE. Answer in 2 sentences maximum."},
    {"role": "user", "content": "What is a zombie process?"}
])

print(response.choices[0].message.content)