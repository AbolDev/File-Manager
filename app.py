from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from captcha.image import ImageCaptcha
from datetime import timedelta
from flask_cors import CORS
import os
import json
import time
import shutil
import random
import datetime
import psutil
import platform
import patoolib
import py7zr
import zipfile
import tarfile
import secrets
# import GPUtil

app = Flask(__name__)
CORS(app)

app.secret_key = secrets.token_hex(16)
# app.secret_key = 'supersecretkey'

VERSION = "0.1.4"

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
        
        file.save(os.path.join(full_path, file.filename))
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

@app.route('/copy', methods=['POST'])
def copy_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    file_path = request.form.get('file_path', '')
    new_path = request.form.get('new_path', '')

    if not file_path or not new_path:
        return jsonify({'error': 'Invalid file path or destination path'}), 400

    try:
        file_path = os.path.join('/', file_path.replace('/', os.sep))
        new_path = os.path.join('/', new_path.replace('/', os.sep))
        
        shutil.copy2(file_path, new_path)
        flash(f'File copied to "{new_path}" successfully!', 'success')
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cut', methods=['POST'])
def cut_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    file_path = request.form.get('file_path', '')
    new_path = request.form.get('new_path', '')

    if not file_path or not new_path:
        return jsonify({'error': 'Invalid file path or destination path'}), 400

    try:
        file_path = os.path.join('/', file_path.replace('/', os.sep))
        new_path = os.path.join('/', new_path.replace('/', os.sep))

        destination_dir = os.path.dirname(new_path)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        shutil.move(file_path, new_path)
        flash(f'File moved to "{new_path}" successfully!', 'success')
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    compression_type = request.form.get('compression_type', 'zip')  # zip, 7z, rar, tar

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
            # elif compression_type == 'rar':
            #     # patoolib.create_archive(output_path, [full_path])
            #     # Prepare the list of files/folders to compress
            #     files_to_archive = []
            #     if os.path.isfile(full_path):
            #         files_to_archive.append(full_path)
            #     elif os.path.isdir(full_path):
            #         for root, dirs, files in os.walk(full_path):
            #             for file in files:
            #                 files_to_archive.append(os.path.join(root, file))
            #     patoolib.create_archive(output_path, files_to_archive)
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
    bt = datetime.datetime.fromtimestamp(boot_time_timestamp)
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

    # gpus = GPUtil.getGPUs()
    # gpu_info = []
    # for gpu in gpus:
    #     gpu_info.append({
    #         "id": gpu.id,
    #         "load": gpu.load * 100,
    #         "memory_free": gpu.memoryFree * (1024 ** 2),
    #         "memory_used": gpu.memoryUsed * (1024 ** 2),
    #         "memory_total": gpu.memoryTotal * (1024 ** 2),
    #         "temperature": gpu.temperature
    #     })

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
            # "cpu_usage_per_core": [psutil.cpu_percent(percpu=True, interval=1)],
            "total_cpu_usage": psutil.cpu_percent(interval=0.15),
        },
        "memory_information": {
            "total": svmem.total,
            "available": svmem.available,
            "used": svmem.used,
            "percentage": svmem.percent
        },
        "disk_information": disk_info,
        # "gpu_information": gpu_info,
    }

    return data

def get_network_info():
    # if_addrs = psutil.net_if_addrs()
    # net_info = {}
    # for interface_name, interface_addresses in if_addrs.items():
    #     addrs = []
    #     for address in interface_addresses:
    #         if str(address.family) == 'AddressFamily.AF_INET':
    #             addrs.append({
    #                 "ip_address": address.address,
    #                 "netmask": address.netmask,
    #                 "broadcast_ip": address.broadcast
    #             })
    #         elif str(address.family) == 'AddressFamily.AF_PACKET':
    #             addrs.append({
    #                 "mac_address": address.address,
    #                 "netmask": address.netmask,
    #                 "broadcast_mac": address.broadcast
    #             })
    #     net_info[interface_name] = addrs

    net_io = psutil.net_io_counters()
    time.sleep(1)
    new_value = psutil.net_io_counters()

    data = {
        "network_information": {
            # "interfaces": net_info,
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
        # return jsonify({"error": "Unauthorized"}), 403

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

@app.route('/system-info')
def system_info_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('system_info.html', version=VERSION)

@app.route('/settings')
def settings_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('settings.html')

if __name__ == '__main__':
    config_ = config()
    port = config_['port']
    app.run(host="0.0.0.0", port=port, debug=True)
