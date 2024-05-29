from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import openai
from sqlalchemy import text
import os
from dotenv import dotenv_values
import requests

import logging
from logging.handlers import RotatingFileHandler

# Setup Flask app
app = Flask(__name__)

# #for Paas
# openai.api_key = os.environ.get('OPENAI_API_KEY')
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

# #for local
openai.api_key = dotenv_values(".env")["OPENAI_API_KEY"]
app.config['SQLALCHEMY_DATABASE_URI'] = dotenv_values(".env")["DATABASE_URL"]

API_KEY = os.environ.get('OPENAI_API_KEY')

db = SQLAlchemy(app)


# Route to fetch surgery numbers
@app.route('/get-surgery-numbers', methods=['GET'])
def get_surgery_numbers():
    try:
        surgery_numbers = db.session.execute(
            text("SELECT DISTINCT ODR_LOGN FROM surgeryrecords")).fetchall()
        surgery_numbers = [num[0] for num in surgery_numbers]
        return jsonify(surgery_numbers)
    except Exception as e:
        return jsonify({"error": str(e)})


def surgery_record_by_ChatGPT(text):
    prompt = """
    {text}

    以上是一位病人的手術紀錄的關鍵字，請你使用以上內容還原成一筆完整的手術紀錄草稿。

    注意，由於我是一位專業的醫生，所以我想要你依照關鍵字先生成一份手術紀錄草稿，我會再更進一步修改，請注意以下幾點：

    1. 在你試著還原出完整的手術紀錄草稿時盡可能的保持明確性和細節的描述，如果關鍵字缺乏敘述導致你只能生產概括內容的話
    你可以在生產完的文章備註你認為我最好可以提供或補充的細節，如：缺少手術切口的確切位置和深度、是否麻醉、傷口處理、傷口位置等等
    不侷限這幾點，因為每位病人進行的手術都不一所以會有不同的狀況。請你也不要完全照這幾個我給你的參考而提供備註。請依照個案。

    1-1. 接續前一點，沒有提供的關鍵字請不要強調Not provided in the record.直接略過就好，可以在最後簡單說如果有提供xxx更好。

    2. 我的習慣是每個步驟都按照手術進行的實際順序進行描述。請你盡可能在某些部分不要顯得冗長或不夠直接。

    3. 我實際的手術紀錄更加簡潔和直接，沒有不必要的擴展或解釋。請你創建的紀錄不要在某些部分可能包含了一些不必要的解釋或背景信息。
    以保持簡潔性。

    4. 請不要用列列點的方式，直接給我一個完整可以閱讀的文章。

    5. 手術紀錄草稿請使用英文原文。回覆內容請直接給我手術紀錄，開頭不要其他內容。

    6.不要自行新增[REDACTED]內容也不要出現任何REDACTED。

    7. 回覆內容請在最後後是否使用英文原文撰寫

    """.format(text=text)

    res = openai.Completion.create(model="gpt-3.5-turbo-instruct",
                                   prompt=prompt,
                                   max_tokens=1500)

    surgery_record = res["choices"][0]["text"].strip()
    return {"surgery_record": surgery_record}


@app.route('/search-results', methods=['POST'])
def search_records():
    data = request.get_json()
    surgery_number = data.get('surgery_number')
    keyword = data.get('keyword')  # Get the keyword from the request

    records = db.session.execute(
        text("""
            SELECT * FROM surgeryrecords 
            WHERE ODR_LOGN = :surgery_number
            LIMIT 2
        """), {
            "surgery_number": surgery_number
        }).fetchall()

    processed_results = []
    for record in records:
        result = {
            "ODR_LOGN": record[0],
            "ODR_CHRT": record[1],
            "ODR_OPP": record[2],
        }
        result["ChatGPT_Surgery_Record"] = surgery_record_by_ChatGPT(
            keyword)["surgery_record"]
        processed_results.append(result)

    return jsonify(processed_results)


# 在您的 Flask 應用設定中添加日誌處理
def setup_logging():
    handler = RotatingFileHandler('flask_app.log',
                                  maxBytes=10000,
                                  backupCount=3)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


setup_logging()


@app.route('/save-changes', methods=['POST'])
def save_changes():
    updates = request.get_json()
    try:
        for update in updates:
            surgery_number = update['surgeryNumber']
            new_record = update['newRecord']

            # 使用 text() 函數將 SQL 語句包裝為文本對象
            query = text(
                "UPDATE surgeryrecords SET new_record = :new_record WHERE ODR_LOGN = :surgery_number"
            )
            db.session.execute(query, {
                'new_record': new_record,
                'surgery_number': surgery_number
            })
            db.session.commit()

        return jsonify({"success": True})
    except Exception as e:
        app.logger.error(f"Error in save_changes: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        result_proxy = db.session.execute(
            text("SELECT * FROM surgeryrecords LIMIT 10"))

        results = result_proxy.fetchall()

        # 如果沒有結果，返回空表格
        if not results:
            return "<p>No records found.</p>"

        # 構建一個 HTML 表格
        html_table = "<table border='1'>"
        html_table += "<tr>"  # 添加表頭
        headers = result_proxy.keys()
        for header in headers:
            html_table += f"<th>{header}</th>"
        html_table += "</tr>"

        for row in results:
            html_table += "<tr>"
            for cell in row:
                html_table += f"<td>{cell}</td>"
            html_table += "</tr>"
        html_table += "</table>"

        return html_table
    except Exception as e:
        return f"Error occurred: {e}"


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    response = requests.post('https://api.openai.com/v1/chat/completions',
                             headers={
                                 'Content-Type': 'application/json',
                                 'Authorization': f'Bearer {API_KEY}'
                             },
                             json={
                                 'model':
                                 'gpt-4',
                                 'messages': [{
                                     'role': 'user',
                                     'content': user_message
                                 }],
                                 'max_tokens':
                                 6000,
                             })

    if response.status_code != 200:
        return jsonify({
            'error':
            response.json().get('error', {}).get('message', 'Unknown error')
        }), response.status_code

    return jsonify(response.json())


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
