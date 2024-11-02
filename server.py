from flask import Flask
from flask import render_template, redirect, url_for, session
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
session_data = {}

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
                    3) Depth: Does the visualization answer the proposed problem? Is the chosen type of visualization (bar chart, line graph, scatter plot, etc.) appropriate for the data and the message it intends to convey?
                    For each, provide a rating 1-5 and a tangible thing in their code they could modify to improve their scoring in this category (if applicable), but without providing direct quotes from the code.
                    Assume the data was found in data.csv and format the response like:
                    1) Clarity: #/5 - suggestion for clarity if applicable.
                    2) Accuracy: #/5 - suggestion for accuracy if applicable.
                    3) Depth: #/5 - suggestion for depth if applicable.'''

ideal_prompt1 = "An interviewee was asked to answer the following data visualization question:\n"
ideal_prompt2 = "\nThey were referencing the following dataset:\n"
ideal_prompt3 = "\nAnd they received this feedback:\n"
ideal_prompt4 = "\nThey may or may not have implemented this feedback since their last answer, but their current code is:\n"
ideal_prompt5 = "\nImplement the feedback on their code if it is still applicable. Assume the data is in data.csv. Return only the code."

resubmit_prompt1 = "You are an expert data analyst and interviewer, interviewing for an entry level data analyst role. An interviewee was given the following dataset:\n\n"
resubmit_prompt2 = "\n\nThey were asked to answer the following question about its contents using data visualization:\n\n"
resubmit_prompt3 = "\n\nThey answered with the following block of code:\n\n"
resubmit_prompt4 = "\n\nAnd they received the following feedback, having been graded on a scale of 1-5 in clarity, accuracy, and depth, each with ssuggestions for improvement:\n\n"
resubmit_prompt5 = "\n\nThey then resubmitted this answer, based on the prior suggestions:\n\n"
resubmit_prompt6 = '''\n\nReassess their scores for clarity, accuracy and depth. They don't necessarily have to have improved. As a reminder, here is how the 3 fields were initially graded:
1) Clarity: Does the visualization effectively communicate the data's message? Is it easy to understand, with appropriate labels, axes, and legends? Does the visualization look visually appealing? Are the color choices, spacing, and overall layout well-designed without sacrificing clarity?
2) Accuracy: Is the data represented accurately? Does the visualization avoid misleading elements, such as distorted scales or selective data omission?
3) Depth: Does the visualization answer the proposed problem? Is the chosen type of visualization (bar chart, line graph, scatter plot, etc.) appropriate for the data and the message it intends to convey?'''
resubmit_prompt7 = '''\n\nYou must provide your feedback in a very specific format. If you do not give a perfect score in any of the given three fields, you have to include an explicit change in their code which would improve their score in this area. These suggestions must not conflict with one another if there are more than one. Use the following format and say nothing except for what is in this format. Replace the lines given with relevant text, using exactly 9 lines:
1) Clarity: #/5 - suggestion for clarity if applicable, related to code below (but should make sense without needing to see the code), or explanation of why they got a 5. Make the suggestion/explanation detailed.
2) Accuracy: #/5 - suggestion for accuracy if applicable, related to code below (but should make sense without needing to see the code), or explanation of why they got a 5. Make the suggestion/explanation detailed.
3) Depth: #/5 - suggestion for depth if applicable, related to code below (but should make sense without needing to see the code), or explanation of why they got a 5. Make suggestion/explanation detailed.
4) a direct quote from the code to be replaced, if there was a suggestion to improve clarity, otherwise write NONE. The text must all be on this line, so use \\n. to represent new lines if necessary.
5) the replacement for the code in the 4th line that would improve their score for clarity, otherwise write NONE. The text must all be on this line, so use \\n. to represent new lines if necessary.
6) a direct quote from the code to be replaced, if there was a suggestion to improve accuracy, otherwise write NONE. The text must all be on this line, so use \\n. to represent new lines if necessary.
7) the replacement for the code in the 6th line that would improve their score for accuracy, otherwise write NONE. The text must all be on this line, so use \\n. to represent new lines if necessary.
8) a direct quote from the code to be replaced, if there was a suggestion to improve depth, otherwise write NONE. The text must all be on this line, so use \\n. to represent new lines if necessary.
9) the replacement for the code in the 8th line that would improve their score for depth, otherwise write NONE. The text must all be on this line, so use \\n. to represent new lines if necessary.'''


@app.route('/resubmit_answer', methods=['GET', 'POST'])
def resubmit_answer():
    global session_data
    data = request.get_json()
    new_answer = data['code'].strip()
    old_answer = session_data['code']
    dataset = session_data['dataset']
    question = session_data['question']
    feedback = "1) Clarity: " + session_data['clarity'] + "\n2) Accuracy: " + session_data['accuracy'] + "\n3) Depth: " + session_data['depth']

    prompt = resubmit_prompt1 + dataset + resubmit_prompt2 + question + resubmit_prompt3 + old_answer + resubmit_prompt4 + feedback + resubmit_prompt5 + new_answer + resubmit_prompt6 + resubmit_prompt7
    print("\n\n", prompt, "\n\n")

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
    print("\n\n\nGPT RESPONSE:\n")
    print(msg)

    uncleaned_lines = msg.splitlines()
    lines = [line.split(') ', 1)[1].strip() for line in uncleaned_lines]

    clarity_score = int(re.search(r'(\d+)', lines[0]).group(0))
    clarity = lines[0].split('- ', 1)[1].strip()

    accuracy_score = int(re.search(r'(\d+)', lines[1]).group(0))
    accuracy = lines[1].split('- ', 1)[1].strip()

    depth_score = int(re.search(r'(\d+)', lines[2]).group(0))
    depth = lines[2].split('- ', 1)[1].strip()

    session_data = {
        'msg': msg,
        'dataset': dataset,
        'question': question,
        'code': new_answer,
        'clarity': clarity,
        'clarity_score': clarity_score,
        'clarity_quote': lines[3],
        'clarity_diff': lines[4],
        'accuracy': accuracy,
        'accuracy_score': accuracy_score,
        'accuracy_quote': lines[5],
        'accuracy_diff': lines[6],
        'depth': depth,
        'depth_score': depth_score,
        'depth_quote': lines[7],
        'depth_diff': lines[8]
    }

    print("\n\Session data:\n")
    print(session_data)

    return jsonify(session_data)


@app.route('/execute_code', methods=['POST'])
def execute_code():
    data = request.get_json()
    code = data["code"]
    id = data["id"]
    dataset = None

    print(f"Executing for question ID {id}...\n\n", code)

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
        dff = dataset.map(lambda x: x.strip() if isinstance(x, str) else x)
        exec(code, {"dataset": dff})
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
    global session_data
    global gpt_feedback
    data = request.get_json()
    id = data['id']
    answer = data['answer'].strip()
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
    clarity = re.search(r'Clarity:.*?(?=\n2\))', msg, re.DOTALL).group(0).split(':', 1)[1].strip()
    accuracy = re.search(r'Accuracy:.*?(?=\n3\))', msg, re.DOTALL).group(0).split(':', 1)[1].strip()
    depth = re.search(r'Depth:.*', msg, re.DOTALL).group(0).split(':', 1)[1].strip()

    # Get the scores
    clarity_match = re.search(r'(\d+)', clarity)
    accuracy_match = re.search(r'(\d+)', accuracy)
    depth_match = re.search(r'(\d+)', depth)
    clarity_score = int(clarity_match.group(0)) if clarity_match else None
    accuracy_score = int(accuracy_match.group(0)) if accuracy_match else None
    depth_score = int(depth_match.group(0)) if depth_match else None

    # Remove the number scores from the suggestions
    clarity = clarity.split('-', 1)[1].strip()
    accuracy = accuracy.split('-', 1)[1].strip()
    depth = depth.split('-', 1)[1].strip()

    gpt_feedback[id] = {
        'question': question,
        'dataset': dataset,
        'feedback': msg,
        'previous_answer': answer
    }

    session_data = {
        'msg': msg,
        'clarity': clarity,
        'accuracy': accuracy,
        'depth': depth,
        'clarity_score': clarity_score,
        'accuracy_score': accuracy_score,
        'depth_score': depth_score,
        'question': question,
        'dataset': dataset,
        'code': answer
    }

    return jsonify(session_data)

    # return jsonify({'msg': msg, 'clarity': clarity, 'accuracy': accuracy, 'insightfulness': insightfulness, 'question': question, 'dataset': dataset, 'code': answer})

@app.route('/feedback')
def feedback():
    return render_template('feedback.html', session_data=session_data)


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
