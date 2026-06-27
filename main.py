import os
import telebot
from google import genai
from google.genai import types
from app import start_server

# 1. Konfigurasi Token (Diambil aman dari Environment Variables Render)
TELEGRAM_TOKEN = os.environ.get("8607503824:AAGZlV1J0oi0o_NEjllTxjc11E8Jc6cDFd0")
GEMINI_API_KEY = os.environ.get("AQ.Ab8RN6JWLV9wcS8Ao-iSSTCLMDiFwZlDrqWdWfyEpC2onC-ANA")
# MASUKKAN CHAT ID TELEGRAM ANDA AGAR BOT TIDAK DIALAHGUNAKAN ORANG LAIN
# Cara tahu ID: Kirim pesan ke bot @userinfobot di Telegram
OWNER_CHAT_ID = 123456789  # Ganti dengan angka Chat ID Anda asli

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Anda adalah asisten AI Sandbox untuk Reverse Engineering. Tugas Anda adalah menganalisis file, kode, 
atau manifes yang dikirimkan. Bedah struktur logika, algoritma, atau indikasi malware jika ada secara objektif.
"""

# Middleware Keamanan
def is_owner(message):
    return message.chat.id == OWNER_CHAT_ID

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_owner(message): return
    bot.reply_to(message, "🤖 **Sandbox AI Cloud Aktif!**\n\nKirimkan pesan teks atau lampiran file (.apk, .txt, .smali, .py) untuk dianalisis.", parse_mode='Markdown')

# Handler Khusus Menerima File Lampiran (Dokumen)
@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not is_owner(message): return
    
    sent_msg = bot.reply_to(message, "📥 *Mengunduh file dari Telegram...*", parse_mode='Markdown')
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Simpan file sementara di server
        local_filename = message.document.file_name
        with open(local_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.edit_message_text("🧠 *Mengunggah file ke Sandbox Gemini AI...*", message.chat.id, sent_msg.message_id, parse_mode='Markdown')
        
        # Unggah file biner ke Gemini API Storage
        gemini_file = ai_client.files.upload(
            file=local_filename,
            config=types.UploadFileConfig(display_name=local_filename)
        )
        
        bot.edit_message_text("⚡ *Menganalisis struktur file & logika kode biner...*", message.chat.id, sent_msg.message_id, parse_mode='Markdown')
        
        # Minta AI menganalisis isi file
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[gemini_file, f"Lakukan reverse engineering pada file {local_filename} ini. Bedah fungsionalitas kodenya."],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2
            )
        )
        
        # Kirim Hasil Ke Pengguna
        bot.edit_message_text(response.text, message.chat.id, sent_msg.message_id, parse_mode='Markdown')
        
        # Bersihkan file lokal setelah selesai
        if os.path.exists(local_filename):
            os.remove(local_filename)
            
    except Exception as e:
        bot.edit_message_text(f"❌ *Gagal memproses file:* `{str(e)}`", message.chat.id, sent_msg.message_id, parse_mode='Markdown')

# Handler Pesan Teks
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if not is_owner(message): return
    sent_msg = bot.reply_to(message, "🧠 *Memproses analisis teks...*", parse_mode='Markdown')
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.2)
        )
        bot.edit_message_text(response.text, message.chat.id, sent_msg.message_id, parse_mode='Markdown')
    except Exception as e:
        bot.edit_message_text(f"❌ *Error:* `{str(e)}`", message.chat.id, sent_msg.message_id, parse_mode='Markdown')

if __name__ == "__main__":
    # Jalankan web server Flask di latar belakang
    start_server()
    print("Bot Telegram berjalan di Cloud...")
    bot.infinity_polling()
