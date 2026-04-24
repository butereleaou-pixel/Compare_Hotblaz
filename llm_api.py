import json
import requests
import re
import time
import re
from tkinter import NONE
import requests
import configparser

with open('config_adjust.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
# 3. 通过字典的键来访问配置 (类型已自动转换)
temperature = config['generate']['temperature']
temperature_compare = config['generate']['temperature_compare']

def call_api(system_prompt, user_content):
  
    url = "https://YOUR_MODEL_API_ADDRESS"
  
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_REAL_API_TOKEN"
    }
  
    data = {
        "model": "YOUR_REAL_MODEL_TYPE",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": temperature,
        "stream": False
    }
  
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result_json = response.json()
    return result_json["choices"][0]["message"]["content"]