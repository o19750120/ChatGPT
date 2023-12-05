from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import openai
from sqlalchemy import text
import os
from dotenv import dotenv_values

# Setup Flask app
app = Flask(__name__)

# Setup OpenAI API
openai.api_key = os.environ.get('OPENAI_API_KEY')
# openai.api_key = dotenv_values(".env")["OPENAI_API_KEY"]

# Setup database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
# app.config['SQLALCHEMY_DATABASE_URI'] = dotenv_values(".env")["DATABASE_URL"]

db = SQLAlchemy(app)


def summarize_record(text):
    prompt = """
    你是一位精通手術的專業醫生，並且擅長將手術紀錄與病人資訊製作成摘要，讓其他醫院醫師可以容易閱讀此病患的手術紀錄，因此對於醫療知識有深入的理解並且能撰寫成益於人理解的手術紀錄。
    ​
    規則：
    ​
    - 手術摘要請用台灣繁體中文表達，翻譯時要準確傳達手術與病人資訊，是整份文件都要經過翻譯，除非有特殊情況。
    ​
    - 保留特定的英文專業術語或手術術語，並在其前後加上空格，例如："中 UN 文"。
    ​
    - 摘要以遵守原意的前提下讓內容更通俗易懂，符合台灣繁體中文的表達習慣。

    - 在編排摘要的文章時，應該按照手術的時間順序和邏輯順序來安排各個部分：

    標題：項目
    病人基本資料：手術序號、病歷號
    手術過程：術式名稱、手術發現、術中發現、手術細節。


    - 所有標題中的項目請使用我接下來提供你的內容，若有項目資料缺失請勿擅自謊報直接略過。手術過程、手術結果這兩個標題中的內容合併製作成摘要並且風格與上述攝護腺增生手術記錄版本的摘要類似，內容也僅限於配合文章編排而微幅修改。

    - 本條消息請勿回覆任何內容，僅需直接打印摘要。

    以下是一筆手術紀錄，包括：
    手術序號、病歷號、日期、術式名稱、手術發現、術中發現、手術細節、術後診斷

    {text}
    """.format(text=text)

    res = openai.Completion.create(model="text-davinci-003",
                                   prompt=prompt,
                                   max_tokens=1000)

    summary = res["choices"][0]["text"].strip()
    return {"summary": summary}


@app.route('/search-results', methods=['POST'])
def search_records():
    # 從請求中提取關鍵字
    data = request.get_json()
    keyword = data['keyword']

    records = db.session.execute(
        text("""
            SELECT * FROM surgeryrecords 
            WHERE ODR_LOGN LIKE :keyword 
            OR ODR_CHRT	LIKE :keyword
            OR ODR_PRDG LIKE :keyword
            OR ODR_FIND LIKE :keyword
            OR ODR_OPF LIKE :keyword
            OR ODR_OPP LIKE :keyword
            OR ODR_PODG LIKE :keyword
            OR ChatGPT LIKE :keyword
            LIMIT 2
        """), {
            "keyword": '%' + keyword + '%'
        }).fetchall()

    # 對每一條記錄進行摘要
    processed_results = []
    for record in records:
        # 摘要生成邏輯，這裡需要您自己實現一個函數
        # summary = summarize_record(record)  # 假設的函數，需要您自己實現

        processed_results.append({
            "ODR_LOGN": record[0],
            "ODR_CHRT": record[1],
            "ODR_PRDG": record[2],
            "ODR_OPF": record[4],
            "ODR_OPP": record[5],
            "ODR_PODG": record[6],
            "ChatGPT": record[7]
            # "summary": summary["summary"]  # 添加摘要
        })

    return jsonify(processed_results)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        results = db.session.execute(
            text("SELECT * FROM surgeryrecords LIMIT 10")).fetchall()
        results_str = '<br>'.join(str(row) for row in results)
        return f"Database is working! Results: <br> {results_str}"
    except Exception as e:
        return f"Error occurred: {e}"


if __name__ == '__main__':
    app.run(debug=True)
