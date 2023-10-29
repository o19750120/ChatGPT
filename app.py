from flask import Flask
import os

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route('/')
def hello_world():
    return 'Hello, World!', openai.api_key
