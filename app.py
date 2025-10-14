from flask import Flask, render_template, request, jsonify
import subprocess

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    question = request.json.get('question')
    
    if question:
        try:
            result = subprocess.check_output(['howdoi', question], stderr=subprocess.STDOUT).decode('utf-8')
            return jsonify({'result': result})
        except subprocess.CalledProcessError as e:
            error_output = e.output.decode('utf-8')
            return jsonify({'result': 'Error: ' + error_output})
        except Exception as e:
            return jsonify({'result': 'Unexpected error occurred: ' + str(e)})
    else:
        return jsonify({'result': 'Unable to process the question'})

if __name__ == '__main__':
    app.run(debug=True)
