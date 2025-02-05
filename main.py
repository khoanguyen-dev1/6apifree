import re
import json
import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from flask_cors import CORS
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

cache = {}
webhook_url = 'https://discord.com/api/webhooks/1335485229766541365/YoQ3lUNedTQb5QnEgMrs7TP-YU673vPnhZDK2r75wYt7dzVvJgcxCEgRgbgSD5Zpe7fo'

relz_key_pattern = r'const\s+keyValue\s*=\s*"([^"]+)"'

async def get_content(url, session, headers=None):
    async with session.get(url, headers=headers, allow_redirects=True) as response:
        html_text = await response.text()
        return html_text

async def fetch_key_value(link):
    urls = [
        link,
        'https://getkey.farrghii.com/check1.php',
        'https://getkey.farrghii.com/check2.php',
        'https://getkey.farrghii.com/check3.php',
        'https://getkey.farrghii.com/finished.php'
    ]
    async with ClientSession() as session:
        for url in urls:
            html_text = await get_content(url, session)
            soup = BeautifulSoup(html_text, 'html.parser')
            script_tags = soup.find_all('script')
            for script_tag in script_tags:
                script_content = script_tag.string
                if script_content:
                    key_match = re.search(relz_key_pattern, script_content)
                    if key_match:
                        return key_match.group(1)
    return None

async def get_user_ip():
    async with ClientSession() as session:
        async with session.get("https://api.ipify.org/") as response:
            ip = await response.text()
            return ip

def send_bypass_notification(url, key_value, user_ip):
    embed = {
        "embeds": [
            {
                "title": "Bypass Notification",
                "description": f"URL: {url}\nUnlocked Key: ```{key_value}```",
                "fields": [
                    {
                        "name": "User IP",
                        "value": user_ip,
                        "inline": True
                    }
                ],
                "color": 3066993,
            }
        ]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(webhook_url, data=json.dumps(embed), headers=headers)
        if response.status_code == 204:
            print("Webhook notification sent successfully.")
        else:
            print(f"Failed to send webhook notification. Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error sending webhook notification: {e}")

@app.route('/bypass', methods=['GET'])
async def get_unlock_url():
    url = request.args.get('url')
    
    if not url:
        return jsonify({'error': 'Missing parameter: url'}), 400

    if url in cache:
        return jsonify({'result': cache[url], 'credit': 'UwU (from cache)'}), 200

    user_ip = await get_user_ip()

    if url.startswith('https://getkey.farrghii.com/'):
        try:
            key_value = await fetch_key_value(url)
            if key_value:
                cache[url] = key_value
                send_bypass_notification(url, key_value, user_ip)
                return jsonify({'result': key_value, 'credit': 'UwU'})
            else:
                return jsonify({'error': 'Key value not found', 'credit': 'UwU'}), 404
        except Exception as e:
            return jsonify({'error': 'An unexpected error occurred', 'credit': 'UwU'}), 500

    elif url.startswith('https://socialwolvez.com/'):
        return await handle_socialwolvez(url, user_ip)

    elif url.startswith('https://rekonise.com/'):
        return await handle_rekonise(url, user_ip)

    elif url.startswith('https://pastebin.com/'):
        return await handle_pastebin(url)

    elif url.startswith('https://paste-drop.com/'):
        return await handle_paste_drop(url)
    
    elif url.startswith('https://pastefy.app/'):
        return await handle_pastefy(url)

    else:
        return jsonify({'error': 'Invalid URL. URL must start with a supported base.'}), 400

async def handle_socialwolvez(url, user_ip):
    try:
        async with ClientSession() as session:
            response = await get_content(url, session)
            soup = BeautifulSoup(response, 'html.parser')
            script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
            if script_tag and script_tag.string:
                try:
                    data = json.loads(script_tag.string)
                    extracted_url = data[5]
                    extracted_name = data[6]

                    if extracted_url and extracted_name:
                        cache[url] = extracted_url
                        send_bypass_notification(url, extracted_url, user_ip)
                        return jsonify({'result': extracted_url, 'name': extracted_name})
                    else:
                        return jsonify({'error': 'Required data not found in the JSON structure.'}), 500

                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    return jsonify({'error': 'Failed to parse JSON data.', 'details': str(e)}), 500
            else:
                return jsonify({'error': 'Script tag with JSON data not found.'}), 404
    except Exception as e:
        return jsonify({'error': 'Failed to make request to the provided URL.', 'details': str(e)}), 500

async def handle_rekonise(url, user_ip):
    try:
        parsed_url = urlparse(url)
        sPathname = parsed_url.path.strip('/')
        api_url = f"https://api.rekonise.com/social-unlocks/{sPathname}/unlock"
        async with ClientSession() as session:
            response = await get_content(api_url, session)
            json_data = json.loads(response)
            key = json_data.get("url")

            if key:
                cache[url] = key
                send_bypass_notification(url, key, user_ip)
                return jsonify({"result": key}), 200
            else:
                return jsonify({"error": "Failed to fetch unlock URL from API"}), 500
    except Exception as e:
        return jsonify({'error': 'Failed to fetch unlock URL.', 'details': str(e)}), 500

async def handle_pastebin(url):
    paste_url = url
    parsed_url = urlparse(paste_url)
    path_parts = parsed_url.path.strip('/').split('/')

    if len(path_parts) < 1:
        return jsonify({'error': 'Invalid URL'}), 400

    paste_id = path_parts[-1]
    raw_url = f'https://pastebin.com/raw/{paste_id}'

    try:
        async with ClientSession() as session:
            response = await get_content(raw_url, session)
            cache[url] = response
            send_bypass_notification(url, response, await get_user_ip())
            return jsonify({'result': response})

    except Exception as e:
        return jsonify({'error': f'Error fetching paste: {str(e)}'}), 500

async def handle_paste_drop(url):
    try:
        async with ClientSession() as session:
            response = await get_content(url, session)
            soup = BeautifulSoup(response, 'html.parser')
            content = soup.find('span', id='content')
            if content:
                parsed_content = content.get_text().replace('\\', '')
                cache[url] = parsed_content
                send_bypass_notification(url, parsed_content, await get_user_ip())
                return jsonify({"status": "success", "result": parsed_content}), 200
            else:
                return jsonify({"status": "fail", "message": "Content not found."}), 404
    except Exception as e:
        return jsonify({"status": "fail", "message": f"Error fetching content: {str(e)}"}), 500

async def handle_pastefy(url):
    parsed_url = urlparse(url)

    if not parsed_url.scheme or not parsed_url.netloc:
        return jsonify({'status': 'error', 'message': 'URL không hợp lệ'}), 400
    
    if '/raw' not in parsed_url.path:
        user_url = f'{url}/raw'
    else:
        user_url = url

    try:
        async with ClientSession() as session:
            response = await get_content(user_url, session)
        if response:
            cache[url] = response
            send_bypass_notification(url, response, await get_user_ip())
            return jsonify({'status': 'success', 'result': response}), 200
        else:
            return jsonify({'status': 'error', 'message': f"Không thể truy cập URL. Mã lỗi: {response.status_code}"}), response.status_code

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
