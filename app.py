from flask import Flask, render_template, request
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def convert():
    input_filename = request.form['input_filename']
    output_filename = request.form['output_filename']

    # Set the working directory to the directory containing convertSoundBank.py
    script_directory = "/Users/pkfrulz/Downloads/freepats-tools-master/freepats-tools"
    os.chdir(script_directory)

    # Run the command
    command = f'python3 {os.path.join(script_directory, "convertSoundBank.py")} {input_filename} {output_filename}'
    subprocess.run(command, shell=True)

    return render_template('index.html', message='Conversion complete!')

if __name__ == '__main__':
    app.run(debug=True)
