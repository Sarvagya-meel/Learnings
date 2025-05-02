from dotenv import load_dotenv
import os
from openai import OpenAI
# Load environment variables from a .env file
load_dotenv()

# Example: Access an environment variable
openAI_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openAI_key)

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": "write a haiku about ai"}
  ]
)

print(completion.choices[0].message)