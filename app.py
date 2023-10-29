import os
from flask import Flask, request, jsonify
import openai
import json

openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)

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


@app.route('/generate-summary', methods=['POST'])
def generate_summary_endpoint():
    data = request.get_json()
    text = data["text"]
    summary = generate_summary(text)
    return jsonify(summary)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
