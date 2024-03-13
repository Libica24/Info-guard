import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

INFO_GUARD_API_KEY = os.environ.get('INFO_GUARD_KEY')
INFO_GUARD_SCAN_URL = 'https://www.infoguard.com/ig/v2/file/scan'
INFO_GUARD_REPORT_URL = 'https://www.infoguard.com/ig/v2/file/report'
INFO_GUARD_URL_SCAN_URL = 'https://www.infoguard.com/ig/v2/url/scan'
INFO_GUARD_URL_REPORT_URL = 'https://www.infoguard.com/ig/v2/url/report'

def scan_file_with_infoguard(file_path):
    params = {'apikey': INFO_GUARD_API_KEY}

    with open(file_path, 'rb') as file:
        files = {'file': (os.path.basename(file_path), file)}

        response = requests.post(INFO_GUARD_SCAN_URL, files=files, params=params)

        if response.status_code == 200:
            json_response = response.json()
            resource = json_response.get('resource')
            if resource:
                return resource
            else:
                return {'error': 'Error submitting file to infoguard'}
        else:
            return {'error': f'Error: {response.status_code}'}

def scan_url_with_infoguard(url):
    params = {'apikey': INFO_GUARD_API_KEY}
    data = {'url': url}

    response = requests.post(INFO_GUARD_URL_SCAN_URL, data=data, params=params)

    if response.status_code == 200:
        json_response = response.json()
        resource = json_response.get('scan_id')
        if resource:
            return resource
        else:
            return {'error': 'Error submitting URL to Infoguard'}
    else:
        return {'error': f'Error: {response.status_code}'}

def get_scan_report(resource, is_url=False):
    params = {'apikey': INFO_GUARD_API_KEY, 'resource': resource}
    report_url = INFO_GUARD_URL_REPORT_URL if is_url else INFO_GUARD_REPORT_URL

    response = requests.get(report_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return {'error': f'Error: {response.status_code}'}

def check_if_already_scanned(file_path=None, url=None):
    if file_path:
        resource = scan_file_with_infoguard(file_path)
    elif url:
        resource = scan_url_with_infoguard(url)
    else:
        return jsonify({'error': 'No file or URL provided'})

    report = get_scan_report(resource, is_url=bool(url))
    return jsonify(report)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    try:
        file = request.files.get('file')
        url = request.form.get('url')

        if file:
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)
            return check_if_already_scanned(file_path=file_path)

        elif url:
            return check_if_already_scanned(url=url)

        else:
            return jsonify({'error': 'No file or URL provided'})

    except Exception as e:
        return jsonify({'error': f'An error occurred: {e}'})

@app.route('/results/<resource>')
def display_results(resource):
    report = get_scan_report(resource)
    return render_template('results.html', report=report)

if __name__ == '__main__':
    app.run(debug=True)
