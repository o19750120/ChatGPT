from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import os

api_key = "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"
openai.api_key = api_key

app = FastAPI()

class TextInput(BaseModel):
    text: str

def generate_summary(text: str) -> dict:
    prompt = """
        根據以下描述的內容，擷取前五個字。

        {text}
    """.format(text=text)

    res = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=100
    )

    summary = res["choices"][0]["text"].strip()

    return {"summary": summary}

@app.post("/generate-summary")
def generate_summary_endpoint(item: TextInput):
    summary = generate_summary(item.text)
    return summary

# 啟動指令如果你使用 uvicorn 來啟動 FastAPI
# uvicorn filename:app --reload
