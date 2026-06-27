import os
import telebot
import subprocess
import shutil
from app import start_server

# Jalankan server Flask paling awal untuk Render
start_server()

TELEGRAM_TOKEN = "8607503824:AAGlyGQFkaOUtmfGQMFgq6VOkycIsRmDHB0"
bot = telebot.TeleBot(TELEGRAM_TOKEN)

OWNER_CHAT_ID = 1209820269  

# Tambahkan folder Java dan Apktool lokal ke sistem Python di Render
HOME_DIR = os.environ.get('HOME', '/opt/render')
os.environ["PATH"] = f"{HOME_DIR}/java/bin:{HOME_DIR}/bin:" + os.environ["PATH"]

def is_owner(message):
    return message.chat.id == OWNER_CHAT_ID

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_owner(message): return
    text = "🤖 **Sandbox Engine Lokal Render Aktif!**\n\nKirimkan file APK Anda (Disarankan di bawah 10MB). Server gratisan Render akan membedah berkas manifest aplikasi secara lokal tanpa batas kuota AI."
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(content_types=['document'])
def handle_apk_render(message):
    if not is_owner(message): return
    
    local_filename = message.document.file_name
    file_extension = os.path.splitext(local_filename).lower()
    
    if file_extension != '.apk':
        bot.reply_to(message, "❌ Alat sandbox lokal ini dirancang khusus untuk berkas .apk.")
        return

    sent_msg = bot.reply_to(message, "📥 Mengunduh biner APK ke server Render...")
    
    try:
        # Unduh berkas APK ke penyimpanan sementara Render
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(local_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.edit_message_text("📦 Memulai Ekstraksi Struktur Manifes via Apktool lokal...", message.chat.id, sent_msg.message_id)
        
        output_dir = "extracted_apk_data"
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
            
        # Eksekusi Apktool dengan memanggil file script lokal yang sudah diunduh tadi
        apktool_bin = f"{HOME_DIR}/bin/apktool"
        subprocess.run([apktool_bin, "d", local_filename, "-o", output_dir, "-f"], check=True)
        
        manifest_path = os.path.join(output_dir, "AndroidManifest.xml")
        
        if os.path.exists(manifest_path):
            bot.edit_message_text("📄 Membaca berkas izin aplikasi dan mencetak laporan...", message.chat.id, sent_msg.message_id)
            
            with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                manifest_content = f.read()
                
            laporan = f"✅ **Hasil Ekstraksi Manifes Lokal ({local_filename})**:\n\n```xml\n" + manifest_content[:3500] + "\n```"
            bot.reply_to(message, laporan, parse_mode="Markdown")
            bot.delete_message(message.chat.id, sent_msg.message_id)
        else:
            bot.edit_message_text("❌ Proses gagal. Berkas AndroidManifest.xml tidak ditemukan.", message.chat.id, sent_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Gagal membongkar APK secara lokal di Render. Error: {str(e)}", message.chat.id, sent_msg.message_id)
        
    finally:
        if os.path.exists(local_filename): os.remove(local_filename)
        if os.path.exists(output_dir): shutil.rmtree(output_dir)

if __name__ == "__main__":
    print("Bot Sandbox Lokal berjalan di Render...")
    bot.infinity_polling()
