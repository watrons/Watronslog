from flask import Flask, request, jsonify
import requests
import re
import json
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Bot token'ınız
BOT_TOKEN = "8430913657:AAES1PEMK4Nk56Isfz33FZlah9UpqBKuMB8"

# Zorunlu kanallar
REQUIRED_CHANNELS = ["@watronschecker", "@nabisystem"]

def is_valid_site(site):
    """Site adının geçerliliğini kontrol et"""
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
    return re.match(pattern, site) is not None

def format_log_message(data, site):
    """API yanıtını formatla"""
    formatted = f"""📊 {site} Log Sorgulama
⏰ {datetime.now().strftime('%H:%M %d %b %a')}
🔗 {site}

"""
    
    if isinstance(data, dict):
        for key, value in data.items():
            formatted += f"🔹 {key}: {value}\n"
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                formatted += f"\n[{i+1}] " + "-"*40 + "\n"
                for key, value in item.items():
                    formatted += f"  {key}: {value}\n"
            else:
                formatted += f"[{i+1}] {item}\n"
    else:
        formatted += f"Veri: {data}\n"
    
    formatted += f"\n" + "="*50 + "\n"
    formatted += "🤖 API-BY-DRAGON\n"
    formatted += f"✅ {REQUIRED_CHANNELS[0]}\n"
    formatted += f"✅ {REQUIRED_CHANNELS[1]}\n"
    
    return formatted

def create_file_content(data, site):
    """Dosya içeriğini oluştur"""
    content = f"""📊 LOG SORGULAMA SONUÇLARI
🔍 Site: {site}
📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⏰ Saat: {datetime.now().strftime('%H:%M %d %b %a')}
🤖 Zorunlu Kanallar: {', '.join(REQUIRED_CHANNELS)}

{'='*50}
\n"""
    
    if isinstance(data, dict):
        for key, value in data.items():
            content += f"{key}: {value}\n"
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                content += f"\n[{i+1}] " + "-"*40 + "\n"
                for key, value in item.items():
                    content += f"  {key}: {value}\n"
            else:
                content += f"[{i+1}] {item}\n"
    else:
        content += f"Veri: {data}\n"
    
    content += f"\n{'='*50}\n"
    content += "🤖 API-BY-DRAGON\n"
    content += f"✅ {REQUIRED_CHANNELS[0]}\n"
    content += f"✅ {REQUIRED_CHANNELS[1]}\n"
    
    return content

def send_telegram_message(chat_id, text):
    """Telegram'a mesaj gönder"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Mesaj gönderilemedi: {e}")
        return None

def send_telegram_document(chat_id, file_content, filename, caption):
    """Telegram'a dosya gönder"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    
    # Dosyayı multipart form-data olarak gönder
    files = {
        'document': (filename, file_content.encode('utf-8'))
    }
    data = {
        'chat_id': chat_id,
        'caption': caption
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        return response.json()
    except Exception as e:
        print(f"Dosya gönderilemedi: {e}")
        return None

def process_log_request(chat_id, site):
    """Log sorgulama işlemini yönet"""
    try:
        # Önce mesaj gönder
        wait_message = send_telegram_message(chat_id, "🔄 Loglar sorgulanıyor...")
        
        # Nabi API'den veri çekme
        api_url = f'https://api.nabi.gt.tc/log?site={site}'
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # 1. Önce mesaj olarak gönder
            message_text = format_log_message(data, site)
            send_telegram_message(chat_id, message_text)
            
            # 2. Sonra dosya olarak gönder
            file_content = create_file_content(data, site)
            filename = f"logs_{site}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            caption = f"📊 {site} Log Sorgulama Sonuçları\n✅ @watronschecker & @nabisystem"
            
            send_telegram_document(chat_id, file_content, filename, caption)
            
            # Bekleme mesajını sil
            if wait_message and 'result' in wait_message:
                message_id = wait_message['result']['message_id']
                delete_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
                delete_data = {
                    'chat_id': chat_id,
                    'message_id': message_id
                }
                requests.post(delete_url, json=delete_data)
                
        else:
            send_telegram_message(chat_id, f"❌ API hatası: {response.status_code}")
            
    except Exception as e:
        send_telegram_message(chat_id, f"❌ Hata oluştu: {str(e)}")

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Log Sorgulama API",
        "version": "1.0",
        "channels": REQUIRED_CHANNELS
    })

@app.route('/log', methods=['GET', 'POST'])
def log_query():
    """Log sorgulama endpoint'i"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            chat_id = data.get('chat_id')
            site = data.get('site')
        else:
            chat_id = request.args.get('chat_id')
            site = request.args.get('site')
        
        if not chat_id or not site:
            return jsonify({
                "status": "error",
                "message": "chat_id ve site parametreleri gereklidir"
            }), 400
        
        if not is_valid_site(site):
            return jsonify({
                "status": "error", 
                "message": "Geçersiz site adı"
            }), 400
        
        # Arka planda işlemi başlat
        thread = threading.Thread(target=process_log_request, args=(chat_id, site))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "success",
            "message": "Sorgu başlatıldı",
            "site": site,
            "chat_id": chat_id
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint'i"""
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '').strip()
            
            if text.startswith('/start'):
                start_text = f"""
🤖 Log Sorgulama Botu

Kullanım:
/log netflix.com
/log exxen.com
/log example.com

⚠️ **ZORUNLU KANALLAR:**
🔹 {REQUIRED_CHANNELS[0]}
🔹 {REQUIRED_CHANNELS[1]}

Komutlar:
/start - Bu mesajı göster
/log <site> - Log sorgula
"""
                send_telegram_message(chat_id, start_text)
                
            elif text.startswith('/log'):
                parts = text.split()
                if len(parts) < 2:
                    send_telegram_message(chat_id, "❌ Lütfen bir site adı girin:\nÖrnek: /log netflix.com")
                else:
                    site = parts[1]
                    if is_valid_site(site):
                        # Arka planda işlemi başlat
                        thread = threading.Thread(target=process_log_request, args=(chat_id, site))
                        thread.daemon = True
                        thread.start()
                    else:
                        send_telegram_message(chat_id, "❌ Geçersiz site adı!")
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        print(f"Webhook hatası: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Webhook'u ayarla"""
    webhook_url = request.args.get('url')
    if not webhook_url:
        return jsonify({"status": "error", "message": "URL gereklidir"})
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    payload = {
        'url': webhook_url
    }
    
    response = requests.post(url, json=payload)
    return jsonify(response.json())

if __name__ == '__main__':
    print("🚀 Flask API başlatılıyor...")
    print(f"📢 Zorunlu kanallar: {', '.join(REQUIRED_CHANNELS)}")
    print("🌐 API endpoint'leri:")
    print("   GET  /          - Durum kontrolü")
    print("   GET  /log       - Log sorgula (chat_id & site parametreleri)")
    print("   POST /log       - Log sorgula (JSON body)")
    print("   POST /webhook   - Telegram webhook")
    print("   GET  /set_webhook - Webhook URL'sini ayarla")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
