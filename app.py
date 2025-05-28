from datetime import datetime, timedelta
import json
import os
import random
import secrets
import shutil
import time
import platform
import requests
import random
import string
import sqlite3
import sys
import io

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from captcha.image import ImageCaptcha

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

import db

import mimetypes
import patoolib
import py7zr
import zipfile
import tarfile
import psutil
import subprocess

debug = False

custom_mime_types = {
    '.webp': 'image/webp',
    '.cpp': 'text/x-c++src',
    '.hpp': 'text/x-c++hdr',
    '.md': 'text/markdown',
    '.json': 'application/json',
    '.yaml': 'application/x-yaml',
    '.toml': 'application/toml',
    '.log': 'text/plain',
    '.bat': 'application/x-msdos-program',
    '.sh': 'application/x-sh',
    '.yml': 'application/x-yaml',
    '.py': 'text/x-python',
    '.java': 'text/x-java-source',
    '.class': 'application/java-vm',
    '.log.tmp': 'text/plain',                   # Log file (temporary)
    '.ini': 'text/plain',                       # Configuration file
    '.sys': 'application/octet-stream',         # System file
    '.cab': 'application/vnd.ms-cab-compressed',# Microsoft Cabinet file
    '.MSI': 'application/x-msi',                # Microsoft Installer file
    '.wsb': 'application/octet-stream',         # Windows Sandbox file
    '.lnk': 'application/x-ms-shortcut',        # Windows Shortcut file
    '.db': 'application/x-sqlite3',             # Database file (SQLite for example)
}

for ext, mime in custom_mime_types.items():
    mimetypes.add_type(mime, ext)

def get_file_mimetype(file_path):
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type if mime_type else 'application/octet-stream'
    except:
        return 'application/octet-stream'

def get_current_time_millis(days=0, hours=0, minutes=0):
    now = datetime.now()
    future_time = now + timedelta(days=days, hours=hours, minutes=minutes)
    future_time_millis = int(future_time.timestamp() * 1000)
    return future_time_millis

def search_in_json(datas, query):
    matches = []
    for i in datas:
        match = all(i.get(key) == value for key, value in query.items())
        if match:
            matches.append(i)
    return matches

app = Flask(__name__)

if debug:
    app.secret_key = 'aaaaaaaaaaaaaaaaaaaaa'
else:
    app.secret_key = secrets.token_hex(16)

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

def config():
    with open("config.json", "rb") as file:
        file_content = file.read()

        config = json.loads(file_content)
        return config

VERSION = config().get("version")

def get_dir(path):
    details = []
    for entry in os.scandir(path):
        try:
            if entry.is_file() or entry.is_dir():
                mod_time = datetime.fromtimestamp(entry.stat().st_mtime)
                mod_time_timestamp = int(mod_time.timestamp())
            else:
                mod_time_timestamp = None

            if entry.is_file():
                size = os.path.getsize(entry.path)
                mimetype = get_file_mimetype(entry.name)
                details.append({
                    'name': entry.name,
                    'mimetype': mimetype,
                    'type': mimetype.split("/")[0] if mimetype else None,
                    'is_dir': False,
                    'size': size,
                    'mod_time_timestamp': mod_time_timestamp,
                    'mod_time': mod_time.strftime('%Y-%m-%d %H:%M:%S') if mod_time_timestamp else 'Unknown'
                })
            elif entry.is_dir():
                subdir_count = sum([1 for _ in os.scandir(entry.path) if _.is_dir()])
                file_count = sum([1 for _ in os.scandir(entry.path) if _.is_file()])
                details.append({
                    'name': entry.name,
                    'is_dir': True,
                    'size': f'{subdir_count} folders, {file_count} files',
                    'mod_time_timestamp': mod_time_timestamp,
                    'mod_time': mod_time.strftime('%Y-%m-%d %H:%M:%S') if mod_time_timestamp else 'Unknown'
                })
        except:
            pass
    return details

def get_parent_directory(path: str):
    if '/' in path:
        return path.rsplit('/', 1)[0]
    return ''

def formatSize(size, decimal_places=1):
    try:
        size = float(size)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB']:
            if size < 1024.0:
                return f"{size:.{decimal_places}f} {unit}"
            size /= 1024.0
        return f"{size:.{decimal_places}f} YB"
    except:
        return size

def create_directory(full_path, directory_name):
    try:
        new_directory_path = os.path.join(full_path, directory_name)
        os.mkdir(new_directory_path)
        flash(f'Directory "{directory_name}" created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating directory: {str(e)}', 'danger')

def check_version():
    try:
        response = requests.get("https://raw.githubusercontent.com/AbolDev/File-Manager/refs/heads/main/config.json")
        response.raise_for_status()
        data = response.json()
        latest_version = data.get("version")
        
        if VERSION < latest_version:
            return True, latest_version
        else:
            return False, latest_version
    except Exception as e:
        return False, str(e)

def gen_random_id(len_ = 16):
    characters = string.ascii_uppercase + string.ascii_lowercase + string.digits + string.digits + string.digits
    random_id = ''.join(random.choices(characters, k=len_))
    while db.get_file_share(random_id=random_id):
        characters = string.ascii_uppercase + string.ascii_lowercase + string.digits + string.digits + string.digits
        random_id = ''.join(random.choices(characters, k=len_))
    return random_id

@app.context_processor
def utility_processor():
    return dict(formatSize=formatSize)

def get_file_details(file_path):
    try:
        if not os.path.isfile(file_path):
            return None

        size = os.path.getsize(file_path)
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        mod_time_timestamp = int(mod_time.timestamp())
        mimetype = get_file_mimetype(os.path.basename(file_path))

        return {
            'name': os.path.basename(file_path),
            'mimetype': mimetype,
            'type': mimetype.split("/")[0] if mimetype else None,
            'is_dir': False,
            'size': size,
            'mod_time_timestamp': mod_time_timestamp,
            'mod_time': mod_time.strftime('%Y-%m-%d %H:%M:%S') if mod_time_timestamp else 'Unknown'
        }
    except Exception as e:
        return None

@app.route('/')
@app.route('/index')
@app.route('/index/')
@app.route('/index/<path:path>')
def index(path=''):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    last_check_date = session.get('last_check_date')
    if last_check_date is None or (datetime.utcnow() - datetime.fromisoformat(last_check_date)) > timedelta(weeks=1):
        is_outdated, version_info = check_version()
        session['last_check_date'] = datetime.utcnow().isoformat()

        if is_outdated:
            flash(f"A new version {version_info} is available! Please update.", 'warning')

    full_path = os.path.join('/', path.replace('/', os.sep))

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        flash('The system cannot find the path specified.', 'danger')
        parent_path = get_parent_directory(path)
        return redirect(url_for('index', path=parent_path))

    files = get_dir(full_path)
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

                    session.permanent = True
                    app.permanent_session_lifetime = timedelta(days=365*100)

                    session['captcha_text'] = None
                    # Setting the default path based on the operating system
                    if platform.system() == 'Linux' and os.geteuid() == 0:
                        default_path = '/root'.replace(os.sep, '/')
                    else:
                        default_path = os.path.expanduser('~').replace(os.sep, '/')
                        if platform.system() == 'Windows':
                            # Remove a drive (such as C:) from the path
                            default_path = default_path.replace('C:', '', 1)
                    return redirect(url_for('index', path=default_path))
                else:
                    flash('Invalid username or password. Please try again.', 'danger')
            else:
                flash('Invalid captcha. Please try again.', 'danger')
        return render_template('login.html', version=VERSION)
    else:
        # If the user is already logged in, they will be redirected to the appropriate path.
        if platform.system() == 'Linux' and os.geteuid() == 0:
            default_path = '/root'.replace(os.sep, '/')
        else:
            default_path = os.path.expanduser('~').replace(os.sep, '/')
            if platform.system() == 'Windows':
                # Remove a drive (such as C:) from the path
                default_path = default_path.replace('C:', '', 1)
        return redirect(url_for('index', path=default_path))

@app.route('/files/<path:current_path>/check_files', methods=['POST'])
def file_manager_check_files(current_path):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    full_path = os.path.join('/', current_path.replace('/', os.sep))
    data = request.get_json()
    file_paths = data.get('file_paths', [])

    try:
        existing_files = []
        for relative_path in file_paths:
            # Prevent Directory Traversal
            if '..' in relative_path or relative_path.startswith('/'):
                continue
            destination_path = os.path.join(full_path, relative_path.replace('/', os.sep))
            if os.path.exists(destination_path):
                existing_files.append(relative_path)
        return jsonify({'success': True, 'existing_files': existing_files})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/files', methods=['GET', 'POST'])
@app.route('/files/<path:current_path>', methods=['GET', 'POST'])
@app.route('/files/', methods=['GET', 'POST'])
def file_manager(current_path=''):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    full_path = os.path.join('/', current_path.replace('/', os.sep))

    if request.method == 'POST':
        if 'complete' in request.form:
            flash('Folder uploaded successfully!', 'success')
            return '', 200

        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['file']
        relative_path = request.form.get('relative_path', file.filename)

        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        # Prevent Directory Traversal
        if '..' in relative_path or relative_path.startswith('/'):
            flash('Invalid file path', 'danger')
            return redirect(request.url)

        # Creating a destination route
        destination_path = os.path.join(full_path, relative_path.replace('/', os.sep))
        destination_dir = os.path.dirname(destination_path)

        try:
            # Create subfolders (including the root folder) if they do not exist
            if destination_dir:
                os.makedirs(destination_dir, exist_ok=True)
            # Save file
            file.save(destination_path)
        except Exception as e:
            flash(f'Error saving file: {str(e)}', 'danger')
            return redirect(request.url)

        return '', 200

    if not os.path.exists(full_path) or not os.path.isdir(full_path):
        flash('The system cannot find the path specified.', 'danger')
        parent_path = get_parent_directory(current_path)
        return redirect(url_for('file_manager', current_path=parent_path))

    files = get_dir(full_path)
    return render_template('file_manager.html', files=files, current_path=current_path, version=VERSION)

@app.route('/show/<path:filename>')
def show(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    full_path = os.path.join('/', filename.replace('/', os.sep))

    return send_file(full_path, mimetype=get_file_mimetype(full_path), as_attachment=False)

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

@app.route('/create_file', methods=['POST'])
def create_file_route():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    current_path = request.form.get('current_path', '')
    file_name = request.form.get('file_name', '')

    if current_path and file_name:
        full_path = os.path.join('/', current_path.replace('/', os.sep))

        os.makedirs(full_path, exist_ok=True)

        file_path = os.path.join(full_path, file_name)

        with open(file_path, 'w') as new_file:
            pass  # Creates an empty file
        
        flash(f'File "{file_name}" created successfully!', 'success')

        return redirect(url_for('file_editor', file_path=file_path))

    return redirect(url_for('file_manager', current_path=current_path))

@app.route('/rename', methods=['POST'])
def rename_item():
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    current_path = request.form.get('current_path', '')
    old_name = request.form.get('old_name', '')
    new_name = request.form.get('new_name', '')

    if current_path and old_name and new_name:
        full_path_old = os.path.join('/', current_path.replace('/', os.sep), old_name)
        full_path_new = os.path.join('/', current_path.replace('/', os.sep), new_name)

        try:
            os.rename(full_path_old, full_path_new)
            return jsonify({
                'success': True,
                'message': f'Item "{old_name}" renamed to "{new_name}" successfully!',
                'new_name': new_name,
                'current_path': current_path
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': False, 'error': 'Invalid input'}), 400

@app.route('/rename_file_editor', methods=['POST'])
def rename_file_editor():
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

        return redirect(url_for('file_editor', file_path=full_path_new))

    flash('The file name did not change.', 'danger')
    return redirect(url_for('file_editor', file_path=full_path_old))

@app.route('/extract', methods=['POST'])
def extract_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    current_path = request.form.get('current_path', '')
    zip_file_name = request.form.get('zip_file_name', '')

    if current_path and zip_file_name:
        full_zip_path = os.path.join('/', current_path.replace('/', os.sep), zip_file_name)

        try:
            if full_zip_path.endswith('.7z'):
                with py7zr.SevenZipFile(full_zip_path, mode='r') as z:
                    z.extractall(path=os.path.dirname(full_zip_path))
                flash(f'7z file "{zip_file_name}" extracted successfully!', 'success')
            else:
                patoolib.extract_archive(full_zip_path, outdir=os.path.dirname(full_zip_path))
                flash(f'File "{zip_file_name}" extracted successfully!', 'success')

        except Exception as e:
            flash(f'Error extracting file: {str(e)}', 'danger')

    return redirect(url_for('file_manager', current_path=current_path))

@app.route('/compression', methods=['POST'])
def compression_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    file_or_folder_path = request.form.get('file_or_folder_path', '')
    compression_type = request.form.get('compression_type', 'zip')

    if file_or_folder_path:
        full_path = os.path.join('/', file_or_folder_path.replace('/', os.sep))

        try:
            if os.path.isfile(full_path):
                file_name = os.path.basename(full_path) + f'.{compression_type}'
                output_path = os.path.join(os.path.dirname(full_path), file_name)
            elif os.path.isdir(full_path):
                file_name = os.path.basename(full_path.rstrip(os.sep)) + f'.{compression_type}'
                output_path = os.path.join(os.path.dirname(full_path), file_name)
            else:
                flash('Invalid path: not a file or folder', 'danger')
                return redirect(url_for('file_manager', current_path=os.path.dirname(full_path)))

            if compression_type == 'zip':
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    if os.path.isfile(full_path):
                        zf.write(full_path, os.path.basename(full_path))
                    elif os.path.isdir(full_path):
                        for root, dirs, files in os.walk(full_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                zf.write(file_path, os.path.relpath(file_path, os.path.dirname(full_path)))
            elif compression_type == '7z':
                with py7zr.SevenZipFile(output_path, mode='w') as archive:
                    if os.path.isfile(full_path):
                        archive.write(full_path, os.path.basename(full_path))
                    elif os.path.isdir(full_path):
                        archive.writeall(full_path, os.path.basename(full_path))
            elif compression_type == 'tar':
                with tarfile.open(output_path, 'w') as tar:
                    if os.path.isfile(full_path):
                        tar.add(full_path, arcname=os.path.basename(full_path))
                    elif os.path.isdir(full_path):
                        tar.add(full_path, arcname=os.path.basename(full_path))
            else:
                flash('Unsupported compression type', 'danger')
                return redirect(url_for('file_manager', current_path=os.path.dirname(full_path)))

            flash(f'Compressed successfully into "{file_name}"!', 'success')

        except Exception as e:
            flash(f'Error compressing files: {str(e)}', 'danger')

    return redirect(url_for('file_manager', current_path=os.path.dirname(full_path)))

def get_system_info():
    uname = platform.uname()
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    cpufreq = psutil.cpu_freq()
    svmem = psutil.virtual_memory()
    partitions = psutil.disk_partitions()
    disk_info = []
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            continue
        disk_info.append({
            "device": partition.device,
            "mountpoint": partition.mountpoint,
            "fstype": partition.fstype,
            "total_size": partition_usage.total,
            "used": partition_usage.used,
            "free": partition_usage.free,
            "percentage": partition_usage.percent
        })

    data = {
        "system_information": {
            "system": uname.system,
            "node_name": uname.node,
            "release": uname.release,
            "version": uname.version,
            "machine": uname.machine,
            "processor": uname.processor,
            "boot_time": f"{bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}"
        },
        "cpu_info": {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency": cpufreq.max,
            "min_frequency": cpufreq.min,
            "current_frequency": cpufreq.current,
            "total_cpu_usage": psutil.cpu_percent(interval=0.15),
        },
        "memory_information": {
            "total": svmem.total,
            "available": svmem.available,
            "used": svmem.used,
            "percentage": svmem.percent
        },
        "disk_information": disk_info,
    }

    return data

def get_network_info():
    net_io = psutil.net_io_counters()
    time.sleep(1)
    new_value = psutil.net_io_counters()

    data = {
        "network_information": {
            "io_stats": {
                "total_bytes_sent": net_io.bytes_sent,
                "total_bytes_received": net_io.bytes_recv,
                "bytes_sent": new_value.bytes_sent - net_io.bytes_sent,
                "bytes_received": new_value.bytes_recv - net_io.bytes_recv
            }
        }
    }

    return data

@app.route('/api/change-username', methods=['POST'])
def change_username():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    new_username = request.form.get('new_username')

    if new_username:
        try:
            config_ = config()
            
            config_['username'] = new_username
            
            with open("config.json", "w") as file:
                json.dump(config_, file)
            
            session.clear()

            flash('Username changed successfully. All users have been logged out.', 'success')
            return jsonify({"message": "Username updated successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid username"}), 400

@app.route('/api/change-password', methods=['POST'])
def change_password():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    new_password = request.form.get('new_password')

    if new_password:
        try:
            config_ = config()
            
            config_['password'] = new_password
            
            with open("config.json", "w") as file:
                json.dump(config_, file)
            
            session.clear()

            flash('Password changed successfully. All users have been logged out.', 'success')
            return jsonify({"message": "Password updated successfully"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid password"}), 400

@app.route('/file_editor/<path:file_path>', methods=['GET', 'POST'])
def file_editor(file_path: str):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    full_path = os.path.join('/', file_path.replace('/', os.sep))

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        flash('The system cannot find the file specified.', 'danger')
        parent_path = os.path.dirname(file_path)
        return redirect(url_for('index', path=parent_path))

    file_name = os.path.basename(file_path)
    directory_path = os.path.dirname(file_path)
    mimetype = get_file_mimetype(full_path)
    is_database = mimetype == 'application/x-sqlite3' or file_name.endswith(('.db', '.sqlite'))

    if is_database and request.method == 'GET':
        try:
            conn = sqlite3.connect(full_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return render_template('file_editor.html', file_path=file_path, file_name=file_name, 
                                 current_path=directory_path, is_database=True, tables=tables, 
                                 version=VERSION)
        except Exception as e:
            flash(f'Error accessing database: {str(e)}', 'danger')
            return redirect(url_for('index', path=directory_path))

    content = ""
    if request.method == 'POST':
        content = request.form.get('content')
        content = content.replace("\r\n", "\n")
        try:
            with open(full_path, 'w', encoding='utf-8') as file:
                file.write(content)
            flash('File saved successfully.', 'success')
            return redirect(url_for('file_editor', file_path=file_path))
        except Exception as e:
            flash(f'Error saving file: {str(e)}', 'danger')

    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except UnicodeDecodeError:
        try:
            with open(full_path, 'rb') as file:
                content = file.read().decode('utf-8', errors='replace')
            flash('File contains invalid UTF-8 characters but was read as binary.', 'warning')
        except Exception as e:
            flash(f'Error reading file: {str(e)}', 'danger')
            content = ''
    except Exception as e:
        flash(f'Error reading file: {str(e)}', 'danger')
        content = ''

    return render_template('file_editor.html', file_path=file_path, file_name=file_name, 
                         current_path=directory_path, content=content, is_database=False, 
                         version=VERSION)

@app.route('/api/database/<path:file_path>/tables/<table_name>', methods=['GET'])
def get_table_data(file_path, table_name):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    full_path = os.path.join('/', file_path.replace('/', os.sep))
    try:
        conn = sqlite3.connect(full_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns_info = cursor.fetchall()
        columns = [col[1] for col in columns_info]
        pk_column = next((col[1] for col in columns_info if col[5] == 1), 'rowid')  # Primary key or rowid

        cursor.execute(f"SELECT {pk_column}, * FROM '{table_name}';")  # Taking pk_column as the first column
        rows = cursor.fetchall()
        conn.close()

        return jsonify({'success': True, 'columns': columns, 'rows': rows, 'pk_column': pk_column})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/database/<path:file_path>/tables/<table_name>/add', methods=['POST'])
def add_table_row(file_path, table_name):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    full_path = os.path.join('/', file_path.replace('/', os.sep))
    data = request.form.to_dict()
    try:
        conn = sqlite3.connect(full_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = [col[1] for col in cursor.fetchall()]
        values = [data.get(col, '') for col in columns]
        placeholders = ','.join(['?' for _ in columns])
        cursor.execute(f"INSERT INTO '{table_name}' ({','.join(columns)}) VALUES ({placeholders});", values)
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Row added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/database/<path:file_path>/tables/<table_name>/update', methods=['POST'])
def update_table_row(file_path, table_name):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    full_path = os.path.join('/', file_path.replace('/', os.sep))
    data = request.form.to_dict()
    pk_value = data.get('old_pk_value')

    try:
        conn = sqlite3.connect(full_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns_info = cursor.fetchall()
        columns = [col[1] for col in columns_info]
        pk_column = next((col[1] for col in columns_info if col[5] == 1), 'rowid')

        valid_columns = [col for col in columns if col != pk_column]  # Remove pk_column from update
        updates = [f"{col}=?" for col in valid_columns]
        values = [data.get(col, '') for col in valid_columns]
        values.append(pk_value)
        sql = f"UPDATE '{table_name}' SET {','.join(updates)} WHERE {pk_column}=?;"

        cursor.execute(sql, values)
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'No rows updated. Check if pk_value exists.'}), 404
        return jsonify({'success': True, 'message': 'Row updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/database/<path:file_path>/tables/<table_name>/delete', methods=['POST'])
def delete_table_row(file_path, table_name):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    full_path = os.path.join('/', file_path.replace('/', os.sep))
    pk_value = request.form.get('pk_value')

    try:
        conn = sqlite3.connect(full_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns_info = cursor.fetchall()
        pk_column = next((col[1] for col in columns_info if col[5] == 1), 'rowid')

        sql = f"DELETE FROM '{table_name}' WHERE {pk_column}=?;"

        cursor.execute(sql, (pk_value,))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'No rows deleted. Check if pk_value exists.'}), 404
        return jsonify({'success': True, 'message': 'Row deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/save_file/<path:file_path>', methods=['POST'])
def save_file(file_path: str):
    if not session.get('logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    full_path = os.path.join('/', file_path.replace('/', os.sep))
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404

    content = request.form.get('content', '').replace("\r\n", "\n")
    try:
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return jsonify({'success': True, 'message': 'File saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error saving file: {str(e)}'}), 500

@app.route('/api/system-info', methods=['GET'])
def system_info():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return jsonify(get_system_info())

@app.route('/api/network-info', methods=['GET'])
def network_info():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return jsonify(get_network_info())

@app.route('/api/add-file-share', methods=['POST'])
def add_file_share():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    path = request.form.get('path')
    file_name = request.form.get('file_name')
    shared_url = request.form.get('shared_url', None) if request.form.get('shared_url') else None
    description = request.form.get('description', None) if request.form.get('description') else None
    total_allowed_requests_per_ip = request.form.get('total_allowed_requests_per_ip', 0) if request.form.get('total_allowed_requests_per_ip') else 0
    total_allowed_requests = request.form.get('total_allowed_requests', 0) if request.form.get('total_allowed_requests') else 0
    total_allowed_download_and_view_per_ip = request.form.get('total_allowed_download_and_view_per_ip', 0) if request.form.get('total_allowed_download_and_view_per_ip') else 0
    total_allowed_download_and_view = request.form.get('total_allowed_download_and_view', 0) if request.form.get('total_allowed_download_and_view') else 0
    name = request.form.get('name', None) if request.form.get('name') else None
    auto_download = request.form.get('auto_download', False) if request.form.get('auto_download') else False

    auto_download = True if auto_download or auto_download == 'on' else False

    if path:
        if not db.get_file_share(shared_url=shared_url):
            full_path = os.path.join('/', path.replace('/', os.sep), file_name)
            is_dir = True if os.path.isdir(full_path) else False
            random_id = gen_random_id()

            if not name:
                name = random_id

            password = None

            db.add_file_share(
                path, file_name, shared_url, is_dir, description,
                total_allowed_requests_per_ip, total_allowed_requests,
                total_allowed_download_and_view_per_ip, total_allowed_download_and_view,
                name, random_id, password, auto_download
            )

            data = {
                'status': True,
                'results': {
                    'random_id': random_id,
                    'shared_url': f'{request.host_url}{shared_url}' if shared_url else None,
                    'file_url': f'{request.host_url}{random_id}',
                    'url': f'{request.host_url}{shared_url}' if shared_url else f'{request.host_url}{random_id}'
                }
            }
        else:
            data = {
                'status': False,
                'error': 'shared_url already exist'
            }
    else:
        data = {
            'status': False,
            'error': 'enter file_or_folder_path'
        }

    return jsonify(data)

@app.route('/system-info')
def system_info_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('system_info.html', version=VERSION)

@app.route('/settings')
def settings_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('settings.html', version=VERSION)

@app.route('/show_file_share/<string:random_id_or_shared_url>')
@app.route('/show_file_share/<string:random_id_or_shared_url>/')
@app.route('/show_file_share/<string:random_id_or_shared_url>/<path:path2>')
def show_file_share(random_id_or_shared_url='', path2=''):
    file_share = db.get_file_share(random_id=random_id_or_shared_url, shared_url=random_id_or_shared_url)

    if file_share:
        if not file_share.total_allowed_download_and_view or file_share.total_allowed_download_and_view > file_share.total_download_and_view:
            if not file_share.total_allowed_download_and_view_per_ip or file_share.total_allowed_download_and_view_per_ip > len(search_in_json(file_share.download_and_view_list, {'ip': request.remote_addr})):
                if file_share.is_dir:
                    full_path = os.path.join('/', file_share.path.replace('/', os.sep), file_share.file_name, path2)
                else:
                    full_path = os.path.join('/', file_share.path.replace('/', os.sep), path2).strip('\\').replace('\\\\', '\\').replace('//', '/').replace('/', os.sep)
                full_path = os.path.normpath(full_path)

                db.update_download_list_to_file_share(file_share.random_id, {'ip': request.remote_addr, 'time': get_current_time_millis()})
                return send_file(full_path, mimetype=get_file_mimetype(full_path), as_attachment=False)

    return '', 403

@app.route('/download_file_share/<string:random_id_or_shared_url>')
@app.route('/download_file_share/<string:random_id_or_shared_url>/')
@app.route('/download_file_share/<string:random_id_or_shared_url>/<path:path2>')
def download_file_share(random_id_or_shared_url='', path2=''):
    file_share = db.get_file_share(random_id=random_id_or_shared_url, shared_url=random_id_or_shared_url)

    if file_share:
        if not file_share.total_allowed_download_and_view or file_share.total_allowed_download_and_view > file_share.total_download_and_view:
            if not file_share.total_allowed_download_and_view_per_ip or file_share.total_allowed_download_and_view_per_ip > len(search_in_json(file_share.download_and_view_list, {'ip': request.remote_addr})):
                if file_share.is_dir:
                    full_path = os.path.join('/', file_share.path.replace('/', os.sep), file_share.file_name, path2)
                else:
                    full_path = os.path.join('/', file_share.path.replace('/', os.sep), path2).strip('\\').replace('\\\\', '\\').replace('//', '/').replace('/', os.sep)
                full_path = os.path.normpath(full_path)

                db.update_download_list_to_file_share(file_share.random_id, {'ip': request.remote_addr, 'time': get_current_time_millis()})
                return send_file(full_path, as_attachment=True)

    return '', 403

@app.route('/<string:random_id_or_shared_url>')
@app.route('/<string:random_id_or_shared_url>/')
@app.route('/<string:random_id_or_shared_url>/<path:path2>')
def file_share(random_id_or_shared_url='', path2=''):
    file_share = db.get_file_share(random_id=random_id_or_shared_url, shared_url=random_id_or_shared_url)

    if file_share:
        if not file_share.total_allowed_requests or file_share.total_allowed_requests > file_share.total_requests_made:
            if not file_share.total_allowed_requests_per_ip or file_share.total_allowed_requests_per_ip > len(search_in_json(file_share.request_list, {'ip': request.remote_addr})):
                full_path = os.path.join('/', file_share.path, file_share.file_name, path2).strip('\\').replace('\\\\', '\\').replace('//', '/').replace('/', os.sep)
                full_path = os.path.normpath(full_path)

                if file_share.is_dir:
                    if not os.path.exists(full_path):
                        flash('The system cannot find the path specified.', 'danger')

                    files = get_dir(full_path)
                else:
                    if file_share.auto_download:
                        return send_file(full_path, as_attachment=True)
                    else:
                        files = [get_file_details(full_path)]

                db.update_request_list_to_file_share(file_share.random_id, {'ip': request.remote_addr, 'time': get_current_time_millis()})
                return render_template('file_share.html', files=files, random_id_or_shared_url=random_id_or_shared_url, path2=path2, version=VERSION, name=file_share.name)

    return '', 403

@app.route('/delete_files', methods=['POST'])
def delete_files():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    filepaths = request.form.getlist('filepaths[]')

    try:
        for filepath in filepaths:
            full_path = os.path.join('/', filepath.replace('/', os.sep))
            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)
        flash(f'{len(filepaths)} item(s) deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting items: {str(e)}', 'danger')

    return jsonify({'success': True}), 200

@app.route('/copy', methods=['POST'])
def copy_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    file_paths = request.form.getlist('file_paths[]')
    new_path = request.form.get('new_path', '')

    if not file_paths or not new_path:
        return jsonify({'error': 'Invalid file paths or destination path'}), 400

    try:
        for file_path in file_paths:
            file_path = os.path.join('/', file_path.replace('/', os.sep))
            new_file_path = os.path.join('/', new_path.replace('/', os.sep), os.path.basename(file_path))
            if os.path.isfile(file_path):
                shutil.copy2(file_path, new_file_path)
            elif os.path.isdir(file_path):
                shutil.copytree(file_path, new_file_path, dirs_exist_ok=True)
        flash(f'{len(file_paths)} item(s) copied to "{new_path}" successfully!', 'success')
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cut', methods=['POST'])
def cut_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    file_paths = request.form.getlist('file_paths[]')
    new_path = request.form.get('new_path', '')

    if not file_paths or not new_path:
        return jsonify({'error': 'Invalid file paths or destination path'}), 400

    try:
        for file_path in file_paths:
            file_path = os.path.join('/', file_path.replace('/', os.sep))
            new_file_path = os.path.join('/', new_path.replace('/', os.sep), os.path.basename(file_path))
            destination_dir = os.path.dirname(new_file_path)
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
            shutil.move(file_path, new_file_path)
        flash(f'{len(file_paths)} item(s) moved to "{new_path}" successfully!', 'success')
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_prompt():
    """Create a terminal prompt"""
    current_dir = session.get('terminal_cwd', os.path.expanduser('~'))
    if platform.system() == 'Windows':
        return f"{current_dir}> "
    else:
        user = os.getlogin()
        host = platform.node()
        home = os.path.expanduser('~')
        display_dir = current_dir.replace(home, '~') if current_dir.startswith(home) else current_dir
        return f"{user}@{host}:{display_dir}$ "

def get_autocomplete_suggestions(prefix: str):
    """Get autocomplete suggestions for paths and files (case-insensitive)"""
    current_dir = session.get('terminal_cwd', os.path.expanduser('~'))
    try:
        if not os.path.isdir(current_dir):
            return []

        prefix = prefix.replace('\\', '/')
        base_path = current_dir
        query = prefix

        if '/' in prefix:
            parts = prefix.rsplit('/', 1)
            if len(parts) == 2 and parts[0]:
                base_path = os.path.normpath(os.path.join(current_dir, parts[0]))
                query = parts[1]
            else:
                query = parts[0]

        if not os.path.isdir(base_path):
            return []

        items = os.listdir(base_path)
        suggestions = [item for item in items if item.lower().startswith(query.lower())]

        if base_path != current_dir:
            relative_base = parts[0] if '/' in prefix else ''
            suggestions = [f"{relative_base}/{item}" if relative_base else item for item in suggestions]
        else:
            suggestions = [item for item in suggestions]

        suggestions.sort(key=str.lower)
        return suggestions
    except Exception as e:
        return []

def run_command(command: str):
    """Execute terminal command while keeping current path"""
    try:
        current_dir = session.get('terminal_cwd', os.path.expanduser('~'))
        if not os.path.isdir(current_dir):
            session['terminal_cwd'] = os.path.expanduser('~')
            current_dir = session['terminal_cwd']

        if command.strip().lower().startswith('cd '):
            new_dir = command[3:].strip()
            if new_dir:
                if os.path.isabs(new_dir):
                    target_dir = new_dir
                else:
                    target_dir = os.path.join(current_dir, new_dir)
                target_dir = os.path.normpath(target_dir)
                if os.path.isdir(target_dir):
                    session['terminal_cwd'] = target_dir
                    return f"Changed directory to {target_dir}"
                else:
                    return f"Error: Directory {target_dir} does not exist"
            else:
                session['terminal_cwd'] = os.path.expanduser('~')
                return f"Changed directory to {session['terminal_cwd']}"
        
        cmd = f'cmd /C "{command}"' if platform.system() == 'Windows' else command
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=current_dir
        )
        stdout, stderr = process.communicate(timeout=30)
        if stderr:
            return stderr

        return stdout or "Command executed successfully."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error: {str(e)}"

@socketio.on('execute_command')
def handle_command(data):
    if not session.get('logged_in'):
        emit('command_output', {'output': 'Error: Unauthorized'})
        return
    command = data.get('command', '').strip()
    if command:
        output = run_command(command)
        emit('command_output', {'output': output})
        emit('prompt', {'prompt': get_prompt()})

@socketio.on('get_prompt')
def send_prompt():
    emit('prompt', {'prompt': get_prompt()})

@socketio.on('autocomplete')
def handle_autocomplete(data):
    prefix = data.get('prefix', '')
    suggestions = get_autocomplete_suggestions(prefix)
    emit('autocomplete', {'suggestions': suggestions})

@app.route('/terminal')
def terminal():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if 'terminal_cwd' not in session:
        session['terminal_cwd'] = os.path.expanduser('~')
    return render_template('terminal.html', version=config().get("version"))

@app.route('/api/check-update', methods=['GET'])
def check_update():
    try:
        # Get current version from VERSION file
        with open('VERSION', 'r') as f:
            current_version = f.read().strip()

        # Get latest version from GitHub
        response = requests.get('https://raw.githubusercontent.com/AbolDev/File-Manager/master/VERSION')
        response.raise_for_status()
        latest_version = response.text.strip()

        update_available = current_version != latest_version
        return jsonify({
            'update_available': update_available,
            'current_version': current_version,
            'latest_version': latest_version
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/apply-update', methods=['POST'])
def apply_update():
    try:
        # Get the absolute path of the project root (where app.py is located)
        project_root = os.path.dirname(os.path.abspath(__file__))
        while not os.path.exists(os.path.join(project_root, 'app.py')):
            project_root = os.path.dirname(project_root)
            if project_root == os.path.dirname(project_root):  # Prevent infinite loop
                raise Exception("Could not find project root containing app.py")

        # Download the latest release as a zip file
        repo_url = 'https://github.com/AbolDev/File-Manager/archive/refs/heads/master.zip'
        response = requests.get(repo_url)
        response.raise_for_status()

        # Extract the zip file
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        extract_path = os.path.join(project_root, 'temp_update')
        zip_file.extractall(extract_path)
        zip_file.close()

        # Find the extracted folder (e.g., File-Manager-master)
        extracted_folder = os.path.join(extract_path, os.listdir(extract_path)[0])

        # Backup critical files (e.g., database)
        db_path = os.path.join(project_root, 'file-manager.db')
        if os.path.exists(db_path):
            shutil.copy2(db_path, os.path.join(project_root, 'file-manager.db.backup'))

        # Replace current files with new ones
        for item in os.listdir(extracted_folder):
            src = os.path.join(extracted_folder, item)
            dst = os.path.join(project_root, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        # Clean up temporary files
        shutil.rmtree(extract_path)

        # Restart the application
        python = sys.executable
        subprocess.Popen([python, os.path.join(project_root, 'app.py')])
        os._exit(0)  # Terminate the current process
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    config_ = config()
    port = int(config_['port'])

    socketio.run(app, host="0.0.0.0", port=port, debug=debug, use_reloader=False)
