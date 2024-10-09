from flask import Flask
from flask import render_template
from flask import Response, request, jsonify
app = Flask(__name__)
import os
from openai import OpenAI
import openai
import base64
import re
import io
import requests
import openai_secrets
client = OpenAI(api_key=openai_secrets.SECRET_KEY)
import json
from base64 import b64decode
from pathlib import Path

new_question_prompt1 = '''
    Create one more entry for a json in the below form. Don't have more than one of any field, e.g. not 2 ids.
    Each should be accompanies by an interesting/difficult question that can be answered about the dataset using dataviz.
    The dataset should have at least 8 entries and relate to the keywords $'''

new_question_prompt2 = '''.
    Think of diverse questions dataviz could be used to ask.
    
    Examples:
    {
        "id": 2,
        "dataset": "Product, Q1 Sales, Q2 Sales, Q3 Sales, Q4 Sales, Yearly Growth, Customer Satisfaction\nElectronics, 150000, 200000, 250000, 300000, 25%, 4.5\nClothing, 50000, 75000, 100000, 125000, 20%, 4.0\nGroceries, 100000, 150000, 200000, 250000, 15%, 4.8\nFurniture, 75000, 100000, 125000, 150000, 10%, 4.1\nToys, 40000, 60000, 90000, 120000, 30%, 4.6\nBooks, 30000, 45000, 70000, 90000, 18%, 4.3",
        "question": "What are the trends in sales across different product categories, and how do these trends correlate with customer satisfaction?",
        "likes": 6
    },
    {
        "id": 3,
        "dataset": "Year, Active Users, New Users, Churn Rate, Revenue, Cost of Acquisition\n2020, 5000, 2000, 5%, 20000, 5000\n2021, 7000, 3000, 4%, 30000, 7000\n2022, 12000, 5000, 6%, 45000, 10000\n2023, 15000, 6000, 3%, 60000, 8000\n2024, 18000, 8000, 2%, 75000, 9000\n2025, 21000, 10000, 1%, 90000, 11000",
        "question": "How has user growth evolved over the years, and what patterns can be identified in user acquisition costs and churn rates?",
        "likes": 7
    },
    {
        "id": 4,
        "dataset": "Date, Temperature, Sales, Customer Traffic, Conversion Rate\n2023-01-01, 30, 1500, 300, 5%\n2023-01-02, 32, 1600, 320, 5.5%\n2023-01-03, 35, 1700, 350, 6%\n2023-01-04, 28, 1400, 280, 4.5%\n2023-01-05, 25, 1300, 250, 4%\n2023-01-06, 40, 2000, 400, 7%\n2023-01-07, 38, 1900, 390, 6.5%\n2023-01-08, 29, 1550, 310, 5.2%",
        "question": "What patterns emerge between temperature changes and customer traffic throughout the week, and how do they affect sales?",
        "likes": 4
    }'''


@app.route('/get_problems', methods=['GET', 'POST'])
def get_problems():
    with open('static/data/questions.json') as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/update_likes', methods=['GET', 'POST'])
def update_likes():
    data = request.get_json()
    id = data['id']
    increment = data['increment']
    with open('static/data/questions.json') as f:
        entries = json.load(f)
    for entry in entries:
        if entry['id'] == id:
            if entry['likes'] + increment >= 0:
                entry['likes'] += increment
                break
            else:
                entries.remove(entry)
                break

    with open('static/data/questions.json', 'w') as f:
        json.dump(entries, f)
    return jsonify(entries)

@app.route('/get_problem', methods=['GET', 'POST'])
def get_problem():
    data = request.get_json()
    id = data['id']
    problem = None
    with open('static/data/questions.json') as f:
        entries = json.load(f)
    for entry in entries:
        if entry['id'] == id:
            problem = entry
            break
    return jsonify(problem)

@app.route('/generate_problem', methods=['GET', 'POST'])
def generate_problem():
    data = request.get_json()
    keywords = data['keywords']
    prompt = new_question_prompt1 + keywords + new_question_prompt2

    # Construct the payload
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "max_tokens": 300
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {client.api_key}"
    }
    
    # Send request to GPT
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_json = response.json()

    # Extract the content field from the response
    content = response_json['choices'][0]['message']['content']
    print("GPT response:\n", content)
    lines = content.splitlines()[1:-1]
    content = '\n'.join(lines)
    modified_json_data = re.sub(r'("dataset":\s*")([^"]*?)\n([^"]*?")', lambda m: m.group(0).replace('\n', '\\n'), content)
    print("\nModified response:\n", modified_json_data)
    data_dict = json.loads(modified_json_data)
    data_dict['likes'] = 0
    print("\n\nParsed Data Dictionary:\n", data_dict)

    # Write in the new json entry
    json_file_path = 'static/data/questions.json'
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    max_id = max(entry['id'] for entry in data) if data else 0
    print("\nNew ID: ", (max_id + 1))
    data_dict['id'] = max_id + 1
    data.append(data_dict)
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)
    return jsonify( {'entryno': max_id + 1} )

@app.route('/')
def home():
    return render_template('home.html')  

if __name__ == '__main__':
    # app.run(debug = True, port = 4000)    
    app.run(debug = True)
