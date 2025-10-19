import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import re
import json
from datetime import datetime
import asyncio

# Bot token'ınız - @BotFather'dan aldığınız token
BOT_TOKEN = "8430913657:AAES1PEMK4Nk56Isfz33FZlah9UpqBKuMB8"

# Zorunlu kanallar
REQUIRED_CHANNELS = ["@watronschecker", "@nabisystem"]

def is_valid_site(site):
    """Site adının geçerliliğini kontrol et"""
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$'
    return re.match(pattern, site) is not None

def format_log_message(data, site):
    """API yanıtını mesaj olarak formatla"""
    formatted = f"""📊 {site} Log Sorgulama
⏰ {datetime.now().strftime('%H:%M %d %b %a')}
🔗 {site}

"""
    
    if isinstance(data, dict):
        for key, value in data.items():
            formatted += f"🔹 {key}: {value}\n"
    elif isinstance(data, list):
        for i, item in enumerate(data[:5]):
            if isinstance(item, dict):
                formatted += f"\n[{i+1}] " + "-"*40 + "\n"
                for key, value in item.items():
                    formatted += f"  {key}: {value}\n"
            else:
                formatted += f"[{i+1}] {item}\n"
    else:
        formatted += f"Veri: {data}\n"
    
    formatted += f"\n" + "="*50 + "\n"
    formatted += "🤖 API-BY-WATRONS\n"
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
    content += "🤖 API-BY-WATRONS\n"
    content += f"✅ {REQUIRED_CHANNELS[0]}\n"
    content += f"✅ {REQUIRED_CHANNELS[1]}\n"
    
    return content

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Başlangıç komutu"""
    start_text = f"""
🤖 Log Sorgulama Botu

Kullanım:
/log netflix.com
/log exxen.com
/log example.com

⚠️ **ZORUNLU KANALLAR:**
🔹 {REQUIRED_CHANNELS[0]}
🔹 {REQUIRED_CHANNELS[1]}

🤖 API-BY-WATRONS

Komutlar:
/start - Bu mesajı göster
/log <site> - Log sorgula
/help - Yardım
"""
    await update.message.reply_text(start_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yardım komutu"""
    help_text = f"""
📖 Bot Kullanım Kılavuzu

Komutlar:
/start - Botu başlat
/log <site> - Site loglarını sorgula
/help - Yardım mesajı

Örnekler:
/log netflix.com
/log exxen.com
/log youtube.com

⚠️ **ZORUNLU KANALLAR:**
🔹 {REQUIRED_CHANNELS[0]}
🔹 {REQUIRED_CHANNELS[1]}

🤖 API-BY-WATRONS

📁 Sonuçlar önce mesaj olarak, sonra dosya olarak gönderilir.
"""
    await update.message.reply_text(help_text)

async def query_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log sorgulama"""
    try:
        message_text = update.message.text.strip()
        
        # /log komutunu ve siteyi ayır
        if message_text.startswith('/log'):
            parts = message_text.split()
            if len(parts) < 2:
                await update.message.reply_text("❌ Lütfen bir site adı girin:\nÖrnek: /log netflix.com")
                return
            
            site = parts[1].strip()
            
            # Site adını doğrula
            if not is_valid_site(site):
                await update.message.reply_text("❌ Geçersiz site adı! Lütfen geçerli bir domain girin.")
                return
            
            # Bekleme mesajı
            wait_msg = await update.message.reply_text("🔄 Loglar sorgulanıyor...")
            
            # Nabi API'den veri çekme
            api_url = f'https://api.nabi.gt.tc/log?site={site}'
            response = requests.get(api_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # 1. Önce mesaj olarak göster
                message_text = format_log_message(data, site)
                await update.message.reply_text(message_text)
                
                # 2. Sonra dosya olarak gönder
                file_content = create_file_content(data, site)
                filename = f"logs_{site}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                await update.message.reply_document(
                    document=file_content.encode('utf-8'),
                    filename=filename,
                    caption=f"📊 {site} Log Sorgulama Sonuçları\n✅ @watronschecker & @nabisystem\n🤖 API-BY-WATRONS"
                )
                
                # Bekleme mesajını sil
                await wait_msg.delete()
                
            else:
                await update.message.reply_text(f"❌ API hatası: {response.status_code}")
                await wait_msg.delete()
                
    except Exception as e:
        await update.message.reply_text(f'❌ Hata oluştu: {str(e)}')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hata yöneticisi"""
    print(f"Hata: {context.error}")
    try:
        await update.message.reply_text("❌ Bir hata oluştu! Lütfen daha sonra tekrar deneyin.")
    except:
        pass

def main():
    """Ana fonksiyon"""
    try:
        print("🤖 Telegram Bot başlatılıyor...")
        
        # Bot uygulamasını oluştur
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Hata yöneticisini ekle
        application.add_error_handler(error_handler)
        
        # Handler'ları ekle
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("log", query_logs))
        
        # /log olmadan da mesajları dinle
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, query_logs))
        
        print("✅ Bot başlatıldı!")
        print(f"📢 Zorunlu kanallar: {', '.join(REQUIRED_CHANNELS)}")
        print("🤖 API-BY-WATRONS")
        print("🔗 Bot şu anda çalışıyor...")
        
        # Botu başlat
        application.run_polling(
            poll_interval=1.0,
            timeout=30,
            drop_pending_updates=True
        )
        
    except Exception as e:
        print(f"❌ Bot başlatılamadı: {e}")
        print("🔁 10 saniye sonra yeniden deneniyor...")
        asyncio.run(asyncio.sleep(10))
        main()

if __name__ == '__main__':
    main()
