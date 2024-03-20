from flask import Flask, render_template, request, jsonify
import subprocess

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    print(request.json)  # Log the entire JSON data received from the client
    question = request.json.get('question')
    
    if question:
        result = subprocess.check_output(['howdoi', question]).decode('utf-8')
        return jsonify({'result': result})
    else:
        return jsonify({'result': 'Unable to process the question'})

if __name__ == '__main__':
    app.run(debug=True)

