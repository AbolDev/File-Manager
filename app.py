from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from werkzeug.utils import secure_filename
from captcha.image import ImageCaptcha
from datetime import timedelta
from flask_cors import CORS
import os
import json
import shutil
import random
import datetime

app = Flask(__name__)
CORS(app)
app.secret_key = 'supersecretkey'
# ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
VERSION = "0.1.1"

def allowed_file(filename):
    # return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    return True

def config():
    with open("config.json", "rb") as file:
        file_content = file.read()

        config = json.loads(file_content)
        return config

def get_parent_directory(path):
    if '/' in path:
        return path.rsplit('/', 1)[0]
    return ''

def formatSize(size, decimal_places=1):
    try:
        size = float(size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.{decimal_places}f} {unit}"
            size /= 1024.0
        return f"{size:.{decimal_places}f} PB"
    except:
        return size

def create_directory(full_path, directory_name):
    try:
        new_directory_path = os.path.join(full_path, directory_name)
        os.mkdir(new_directory_path)
        flash(f'Directory "{directory_name}" created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating directory: {str(e)}', 'danger')

@app.context_processor
def utility_processor():
    return dict(formatSize=formatSize)

def get_file_details(path):
    details = []
    for entry in os.scandir(path):
        try:
            if entry.is_file():
                size = os.path.getsize(entry.path)
                mod_time = datetime.datetime.fromtimestamp(entry.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                details.append({
                    'name': entry.name,
                    'type': 'File',
                    'size': size,
                    'mod_time': mod_time
                })
            elif entry.is_dir():
                subdir_count = sum([1 for _ in os.scandir(entry.path) if _.is_dir()])
                file_count = sum([1 for _ in os.scandir(entry.path) if _.is_file()])
                mod_time = datetime.datetime.fromtimestamp(entry.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                details.append({
                    'name': entry.name,
                    'type': 'Directory',
                    'size': f'{subdir_count} folders, {file_count} files',
                    'mod_time': mod_time
                })
        except:
            pass
    return details

@app.route('/')
@app.route('/<path:path>')
def index(path=''):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    full_path = os.path.join('/', path.replace('/', os.sep))

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        flash('The system cannot find the path specified.', 'danger')
        parent_path = get_parent_directory(path)
        return redirect(url_for('index', path=parent_path))

    files = get_file_details(full_path)
    return render_template('index.html', files=files, current_path=path, version=VERSION)

def random_number_without_1_and_7():
    allowed_digits = [0, 2, 3, 4, 5, 6, 8, 9]
    number = ""
    for _ in range(5):
        digit = random.choice(allowed_digits)
        number += str(digit)
    
    while number[0] == '0':
        number = str(random.choice(allowed_digits[1:])) + number[1:]
    
    return number

@app.route('/captcha', methods=['GET', 'POST'])
def captcha_gen():
    # captcha_text = str(random.randint(10000, 99999))
    captcha_text = random_number_without_1_and_7()
    captcha = ImageCaptcha()
    captcha_image = captcha.generate(captcha_text)
    img_bytes = captcha_image.getvalue()
    session['captcha_text'] = captcha_text
    return img_bytes

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not session.get('logged_in'):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            captcha = request.form['captcha']
            if str(captcha) == session.get('captcha_text'):
                config_ = config()
                if username == config_['username'] and password == config_['password']:
                    session['logged_in'] = True
                    flash('Logged in successfully!', 'success')

                    # Set session['logged_in'] to permanent
                    session.permanent = True
                    app.permanent_session_lifetime = timedelta(days=365*100)

                    session['captcha_text'] = None
                    return redirect(url_for('index'))
                else:
                    flash('Invalid username or password. Please try again.', 'danger')
            else:
                flash('Invalid captcha. Please try again.', 'danger')
        return render_template('login.html', version=VERSION)
    else:
        return redirect(url_for('index'))

@app.route('/files', methods=['GET', 'POST'])
@app.route('/files/<path:current_path>', methods=['GET', 'POST'])
@app.route('/files/', methods=['GET', 'POST'])
def file_manager(current_path=''):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    full_path = os.path.join('/', current_path.replace('/', os.sep))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(full_path, filename))
            flash('File uploaded successfully!', 'success')
            return redirect(request.url)

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        flash('The system cannot find the path specified.', 'danger')
        parent_path = get_parent_directory(current_path)
        return redirect(url_for('file_manager', current_path=parent_path))

    files = get_file_details(full_path)
    return render_template('file_manager.html', files=files, current_path=current_path, version=VERSION)

@app.route('/download/<path:filename>')
def download_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    full_path = os.path.join('/', filename.replace('/', os.sep))
    return send_file(full_path, as_attachment=True)

@app.route('/logout')
def logout():
    session['logged_in'] = False
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/create_directory', methods=['POST'])
def create_directory_route():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    current_path = request.form.get('current_path', '')
    directory_name = request.form.get('directory_name', '')

    if current_path and directory_name:
        full_path = os.path.join('/', current_path.replace('/', os.sep))
        create_directory(full_path, directory_name)

    return redirect(url_for('file_manager', current_path=current_path))

@app.route('/delete_directory/<path:dirpath>', methods=['DELETE'])
def delete_directory_route(dirpath):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    full_path = os.path.join('/', dirpath.replace('/', os.sep))

    try:
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
            flash(f'Directory "{dirpath}" deleted successfully!', 'success')
        else:
            flash(f'Directory "{dirpath}" not found.', 'danger')
    except Exception as e:
        flash(f'Error deleting directory: {str(e)}', 'danger')

    return '', 204

@app.route('/delete_file/<path:filepath>', methods=['DELETE'])
def delete_file(filepath):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    full_path = os.path.join('/', filepath.replace('/', os.sep))

    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
            flash(f'File "{filepath}" deleted successfully!', 'success')
        else:
            flash(f'File "{filepath}" not found.', 'danger')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'danger')

    return '', 204

@app.route('/rename', methods=['POST'])
def rename_item():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    current_path = request.form.get('current_path', '')
    old_name = request.form.get('old_name', '')
    new_name = request.form.get('new_name', '')

    if current_path and old_name and new_name:
        full_path_old = os.path.join('/', current_path.replace('/', os.sep), old_name)
        full_path_new = os.path.join('/', current_path.replace('/', os.sep), new_name)

        try:
            os.rename(full_path_old, full_path_new)
            flash(f'Item "{old_name}" renamed to "{new_name}" successfully!', 'success')
        except Exception as e:
            flash(f'Error renaming item: {str(e)}', 'danger')

    return redirect(url_for('file_manager', current_path=current_path))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
