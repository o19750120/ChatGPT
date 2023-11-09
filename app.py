from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import openai
from sqlalchemy import text
import os



# Setup Flask app
app = Flask(__name__)

# Setup OpenAI API
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Setup database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)


def summarize_record(text):
    prompt = """
    以下是一筆手術紀錄，包括：
    手術序號、病歷號、日期、術式名稱、手術發現、術中發現、手術細節、術後診斷
    請針對這筆手術紀錄製作一個摘要。

        {text}
    """.format(text=text)

    res = openai.Completion.create(model="text-davinci-003",
                                   prompt=prompt,
                                   max_tokens=200)

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
        """), {
            "keyword": '%' + keyword + '%'
        }).fetchall()

    # 對每一條記錄進行摘要
    processed_results = []
    for record in records:
        # 摘要生成邏輯，這裡需要您自己實現一個函數
        summary = summarize_record(record)  # 假設的函數，需要您自己實現

        processed_results.append({
            "ODR_LOGN": record[0],
            "ODR_CHRT": record[1],
            "ODR_PRDG": record[2],
            "ODR_FIND": record[3],
            "ODR_OPF": record[4],
            "ODR_OPP": record[5],
            "ODR_PODG": record[6],
            "summary": summary["summary"]  # 添加摘要
        })

    app.logger.debug(summary)

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

