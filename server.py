from flask import Flask
from flask import render_template
from flask import Response, request, jsonify, send_file
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
openai.api_key = openai_secrets.SECRET_KEY
import json
from base64 import b64decode
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import traceback
from io import StringIO
import matplotlib
matplotlib.use('Agg')
import sys

gpt_feedback = {}

new_question_prompt1 = '''Create one more entry for a json in the below form. Don't have more than one of any field, e.g. not 2 ids.
    Each should be accompanies by an interesting/difficult question that can be answered about the dataset using dataviz.
    The dataset should have at least 8 entries and relate to the keywords.'''

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

submit_prompt1 = "An interview candidate was asked the following question:\n"
submit_prompt2 = "\nThey were analyzing this dataset:\n"
submit_prompt3 = "\nAnd this was their answer in Python:\n"
submit_prompt4 = '''\nYou must rate their solution in three categories:
                    1) Clarity: Does the visualization effectively communicate the data's message? Is it easy to understand, with appropriate labels, axes, and legends? Does the visualization look visually appealing? Are the color choices, spacing, and overall layout well-designed without sacrificing clarity?
                    2) Accuracy: Is the data represented accurately? Does the visualization avoid misleading elements, such as distorted scales or selective data omission?
                    3) Insightfulness: Does the visualization answer the proposed problem? Is the chosen type of visualization (bar chart, line graph, scatter plot, etc.) appropriate for the data and the message it intends to convey?
                    For each, provide a rating 1-5 and a tangible thing in their code they could modify to improve their scoring in this category (if applicable).
                    Assume the data was found in data.csv and format the response like:
                    1) Clarity: #/5
                    Suggestion for clarity if applicable.
                    2) Accuracy #/5
                    Suggestion for accuracy if applicable.
                    3) Insightfulness: #/5
                    Suggestion for insightfulness if applicable.'''

ideal_prompt1 = "An interviewee was asked to answer the following data visualization question:\n"
ideal_prompt2 = "\nThey were referencing the following dataset:\n"
ideal_prompt3 = "\nAnd they received this feedback:\n"
ideal_prompt4 = "\nThey may or may not have implemented this feedback since their last answer, but their current code is:\n"
ideal_prompt5 = "\nImplement the feedback on their code if it is still applicable. Assume the data is in data.csv. Return only the code."

@app.route('/execute_code', methods=['POST'])
def execute_code():
    code = request.json.get("code")
    id = request.json.get("id")
    dataset = None

    print("Executing...\n\n", code)

    with open('static/data/questions.json') as f:
        entries = json.load(f)
        
    for entry in entries:
        if entry['id'] == id:
            dataset = entry['dataset']

    if not code:
        print('Error: no code')
        return {"error": "No code provided"}, 400
    
    if not dataset:
        print('Error: no dataset')
        return {"error": "No dataset"}, 400

    output_buffer = io.StringIO()
    try:
        old_stdout = sys.stdout
        sys.stdout = output_buffer
        dataset = pd.read_csv(StringIO(dataset))
        dataset.columns = dataset.columns.str.strip()
        df = dataset.map(lambda x: x.strip() if isinstance(x, str) else x)
        exec(code, {"dataset": df})
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        # Encode image to base64
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        return jsonify({
            'image': image_base64,
            'output': output_buffer.getvalue()
        })
    except Exception as e:
        print('Error: code didn\'t execute')
        traceback.print_exc() 
        tb = traceback.format_exc()
        return {"error": str(e), "output": output_buffer.getvalue(), "traceback": tb}, 500
    finally:
        sys.stdout = old_stdout

@app.route('/get_ideal_viz', methods=['GET', 'POST'])
def get_ideal_viz():
    global gpt_feedback
    data = request.get_json()
    id = data['id']
    answer = data['answer']

    prompt = ideal_prompt1 + gpt_feedback[id]['question'] + ideal_prompt2 + gpt_feedback[id]['dataset'] + ideal_prompt3 + gpt_feedback[id]['feedback'] + ideal_prompt4 + answer + ideal_prompt5
    print(prompt, "\n\n")

    response = openai.chat.completions.create(
        model = 'gpt-4o',
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    msg = response.choices[0].message.content
    print(msg)

    return jsonify({"msg": msg})
        

@app.route('/submit_answer', methods=['GET', 'POST'])
def submit_answer():
    global gpt_feedback
    data = request.get_json()
    id = data['id']
    answer = data['answer']
    question = ""
    dataset = ""

    with open('static/data/questions.json') as f:
        entries = json.load(f)
    for entry in entries:
        if entry['id'] == int(id):
            question = entry['question']
            dataset = entry['dataset']

    prompt = submit_prompt1 + question + submit_prompt2 + dataset + submit_prompt3 + answer + submit_prompt4
    print(prompt, "\n\n")

    response = openai.chat.completions.create(
        model = 'gpt-4o',
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    msg = response.choices[0].message.content
    print(msg)

    # Use regex to extract each section without numbers and labels
    clarity = re.search(r'Clarity:.*?(?=\n2\))', msg, re.DOTALL).group(0).replace('1) Clarity:', '').strip()
    accuracy = re.search(r'Accuracy:.*?(?=\n3\))', msg, re.DOTALL).group(0).replace('2) Accuracy:', '').strip()
    insightfulness = re.search(r'Insightfulness:.*', msg, re.DOTALL).group(0).replace('3) Insightfulness:', '').strip()

    gpt_feedback[id] = {
        'question': question,
        'dataset': dataset,
        'feedback': msg,
        'previous_answer': answer
    }

    return jsonify({'msg': msg, 'clarity': clarity, 'accuracy': accuracy, 'insightfulness': insightfulness})




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
