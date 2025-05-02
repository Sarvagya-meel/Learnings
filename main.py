from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

# Example: Access an environment variable
my_var = os.getenv("OPENAI_API_KEY")

if my_var is None:
    print("Environment variable not found.")

print("Hello, World!"+ str(my_var))