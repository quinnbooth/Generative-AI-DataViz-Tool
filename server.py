from flask import Flask
from flask import render_template
from flask import Response, request, jsonify
app = Flask(__name__)
import os
from openai import OpenAI
import openai
import base64
import io
import requests
import openai_secrets
client = OpenAI(api_key=openai_secrets.SECRET_KEY)
import json
from base64 import b64decode
from pathlib import Path


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
        if entry['id'] == id and entry['likes'] + increment >= 0:
            entry['likes'] += increment
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

# OLD \/\/\/

count = 1

palette_data = {
    "names": [0],
    "colors": [
        ["#FF6347", "#4682B4", "#32CD32", "#FF4500", "#8A2BE2"]
    ],
    "generations": [
        None
    ]
}



@app.route('/get_preview', methods=['GET', 'POST'])
def get_preview():
    global palette_data
    palette = " ".join(request.get_json().get('colors'))
    name = request.get_json().get('name')
    print(name)
    print(palette)

    p = "generate an image of a simple website homepage that only uses these colors: " + palette
    response_image = client.images.generate(
        prompt=p,
        n=1,
        size="256x256",
    )

    url = response_image.data[0].url

    image = [
        {
            "prompt": p,
            "url": url, #image_file.as_posix(),
        }
    ]
    
    palette_data['generations'][name] = image

    print(palette_data)

    # #just send new images
    return jsonify(palette_data)

@app.route('/get_colors', methods=['GET', 'POST'])
def get_colors():

    global palette_data
    global count

    file = request.files['image']
    image_bytes = file.read()
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    prompt = (
        "Provide me a color palette of 5 different hex colors, each on a new line, without any extra text other than the color palette. Example:\n"
        "#000000\n"
        "#00000f\n"
        "#0000ff\n"
        "#000fff\n"
        "#00ffff"
    )
    
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
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
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
    
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_json = response.json()
    print(response_json)

    # Extract the content field from the response
    content = response_json['choices'][0]['message']['content']

    # Split the content by new lines and strip any extra spaces
    color_codes = [color.strip() for color in content.split('\n') if color.strip()]
    palette_data['colors'].append(color_codes)
    palette_data['names'].append(count)
    palette_data['generations'].append(None)
    count += 1

    return jsonify(palette_data)


@app.route('/')
def home():
    return render_template('home.html', data=palette_data)   


if __name__ == '__main__':
    # app.run(debug = True, port = 4000)    
    app.run(debug = True)




