from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import openai
from dotenv import dotenv_values
from sqlalchemy import text

# Setup Flask app
app = Flask(__name__)

# Setup OpenAI API
config = dotenv_values(".env")
openai.api_key = config["api_key"]

# Setup database
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/手術紀錄_test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://uquntbssh5qjxz3c:1sCSa0lO9EivSndeMEih@bipiwnp5zpch7rxjkw91-mysql.services.clever-cloud.com:3306/bipiwnp5zpch7rxjkw91'

db = SQLAlchemy(app)

# Function to generate summary using OpenAI
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

# Endpoint for generating summary
@app.route('/generate-summary', methods=['POST'])
def generate_summary_endpoint():
    data = request.get_json()
    text = data["text"]
    summary = generate_summary(text)
    return jsonify(summary)

# Main endpoint for your application
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form['t1']
        results = db.session.execute(
            text("""
                SELECT * FROM surgeryrecords 
                WHERE surgery_name LIKE :keyword 
                OR patient_gender LIKE :keyword
                OR surgery_summary LIKE :keyword
            """),
            {"keyword": '%' + keyword + '%'}).fetchall()
        return render_template('index.html', results=results)
    return render_template('index.html')

# New route for testing database
@app.route('/test-db', methods=['GET'])
def test_db():
    try:
        # For the purpose of testing, we'll just fetch the first 10 rows
        results = db.session.execute(text("SELECT * FROM surgeryrecords LIMIT 10")).fetchall()
        # Convert the results to string for simple display
        results_str = '<br>'.join(str(row) for row in results)
        return f"Database is working! Results: <br> {results_str}"
    except Exception as e:
        return f"Error occurred: {e}"


