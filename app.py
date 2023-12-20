import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'flac_files'
SFZ_FOLDER = 'sfz_files'
SF2_FOLDER = 'sf2_files'  # New folder for SF2 files
ALLOWED_EXTENSIONS = {'wav', 'flac', 'sfz'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['SFZ_FOLDER'] = SFZ_FOLDER
app.config['SF2_FOLDER'] = SF2_FOLDER  # Added SF2 folder

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_wav_to_flac(input_folder, output_folder):
    for filename in os.listdir(input_folder):
        if filename.endswith(".wav"):
            base_name, _ = os.path.splitext(filename)
            flac_filename = f"{base_name}.flac"
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, flac_filename)
            # Use ffmpeg for lossless conversion
            command = ["ffmpeg", "-i", input_path, "-y", "-f", "flac", output_path]
            subprocess.call(command)
            print(f"Converted {filename} to {flac_filename}")

def create_sfz_and_convert(wav_folder, sfz_filename, sfz_folder, sf2_folder):
    convert_wav_to_flac(wav_folder, sfz_folder)
    
    sfz_content = """<group>
pitch_keytrack=0
ampeg_release=1.000

"""
    flac_files = [file for file in os.listdir(sfz_folder) if file.endswith(".flac")]
    
    for i, flac_filename in enumerate(sorted(flac_files)):
        sfz_content += f'<region> sample={flac_filename}\nlokey={i+1}\nhikey={i+1}\npitch_keycenter=60\nloop_mode=no_loop\n\n'

    sfz_filepath = os.path.join(sfz_folder, sfz_filename + ".sfz")
    with open(sfz_filepath, 'w') as sfz_file:
        sfz_file.write(sfz_content)

    sf2_filename = f"{sfz_filename}.sf2"
    sf2_filepath = os.path.join(sf2_folder, sf2_filename)
    
    sf2_command = ["python3", "convertSoundBank.py", sfz_filepath, sf2_filepath]
    subprocess.call(sf2_command)

    # Clean sfz_files and uploads folders
    for file in os.listdir(sfz_folder):
        file_path = os.path.join(sfz_folder, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

    for file in os.listdir(wav_folder):
        file_path = os.path.join(wav_folder, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

    return sfz_filepath, sf2_filepath

@app.route('/', methods=['GET', 'POST'])
def index():
    sfz_sf2_created_message = None  # Variable to store SFZ and SF2 created message

    if request.method == 'POST':
        if 'upload' in request.form:
            # Handle file upload
            files = request.files.getlist('files[]')
            for file in files:
                if file and allowed_file(file.filename):
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

            return redirect(url_for('index'))

        elif 'create_sfz' in request.form:
            # Handle SFZ file creation and conversion
            sfz_filename = request.form['sfz_filename']
            sfz_filepath, sf2_filepath = create_sfz_and_convert(app.config['UPLOAD_FOLDER'], sfz_filename, app.config['SFZ_FOLDER'], app.config['SF2_FOLDER'])
            sfz_sf2_created_message = f'SFZ and SF2 files created! Check the <a href="{url_for("download_sfz", filename=sfz_filename)}">generated SFZ file</a> and <a href="{url_for("download_sf2", filename=os.path.basename(sf2_filepath))}">generated SF2 file</a>.'

    return render_template('index.html', sfz_sf2_created_message=sfz_sf2_created_message)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/downloads/<filename>')
def download_sfz(filename):
    return send_from_directory(app.config['SFZ_FOLDER'], filename + ".sfz")

@app.route('/downloads_sf2/<filename>')
def download_sf2(filename):
    return send_from_directory(app.config['SF2_FOLDER'], filename)


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    if not os.path.exists(SFZ_FOLDER):
        os.makedirs(SFZ_FOLDER)
    if not os.path.exists(SF2_FOLDER):
        os.makedirs(SF2_FOLDER)
    app.run(debug=True, port=5006)