import requests
import base64
import json
import streamlit as st

GITHUB_TOKEN = st.secrets["GitHub"]["apikey"]
REPO = "AzeemChaudhry/attendance_merger"
BRANCH = "main"

def github_request(method, url, data=None, headers=None):
    response = requests.request(method, url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

def get_file_content(file_path):
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}?ref={BRANCH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    content = response.json()
    file_content = base64.b64decode(content['content']).decode('utf-8')
    return file_content, content['sha']

def update_file(file_path, content, sha):
    url = f"https://api.github.com/repos/{REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "message": "Update attendance",
        "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    response = requests.put(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
