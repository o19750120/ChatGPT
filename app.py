from flask import Flask
import os
import openai

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route('/')
def hello_world():
    return 'Hello, World!' + "api_key=" + openai.api_key

def generate_summary(text):
    prompt = """
        根據以下描述的內容，擷取前五個字。

        {text}
    """.format(text=text)

    res = openai.Completion.create(
        model = "text-davinci-003",
        prompt = prompt,
        max_tokens = 100
    )

    summary = res["choices"][0]["text"].strip()

    return {"summary": summary}
