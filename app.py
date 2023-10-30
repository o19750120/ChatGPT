from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import openai
from dotenv import dotenv_values
from sqlalchemy import text

# Setup Flask app
app = Flask(__name__)

# Setup OpenAI API
config = dotenv_values(".env")
openai.api_key = config["OPENAI_API_KEY"]

# Setup database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://uquntbssh5qjxz3c:1sCSa0lO9EivSndeMEih@bipiwnp5zpch7rxjkw91-mysql.services.clever-cloud.com:3306/bipiwnp5zpch7rxjkw91'
db = SQLAlchemy(app)

def generate_summary(text):
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

@app.route('/search-results', methods=['POST'])
def search_results():
    keyword = request.json['keyword']
    results = db.session.execute(
        text("""
            SELECT * FROM surgeryrecords 
            WHERE surgery_name LIKE :keyword 
            OR patient_gender LIKE :keyword
            OR surgery_summary LIKE :keyword
        """),
        {"keyword": '%' + keyword + '%'}).fetchall()

    processed_results = []
    for result in results:
        summary = generate_summary(result[4])
        processed_result = list(result)
        processed_result[4] = summary['summary']
        processed_results.append(processed_result)

    return jsonify(processed_results)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        results = db.session.execute(text("SELECT * FROM surgeryrecords LIMIT 10")).fetchall()
        results_str = '<br>'.join(str(row) for row in results)
        return f"Database is working! Results: <br> {results_str}"
    except Exception as e:
        return f"Error occurred: {e}"
