import os
import telebot
from google import genai
from google.genai import types
from app import start_server

# Jalankan server Flask paling awal untuk Render
start_server()

# 1. Konfigurasi Kunci Akses (Gunakan API Key Gemini dari Environment Variables)
TELEGRAM_TOKEN = "8607503824:AAH-JrEMPRkzXMYW62w4YrPpn_hOKlhF9Vw"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ID Pemilik Bot Anda
OWNER_CHAT_ID = 1209820269  

# 2. Inisialisasi Pustaka
bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Anda adalah asisten AI Sandbox untuk Reverse Engineering. Tugas Anda adalah menganalisis file, kode, 
atau manifes yang dikirimkan. Bedah struktur logika, algoritma, atau indikasi malware jika ada secara objektif.
"""

def is_owner(message):
    return message.chat.id == OWNER_CHAT_ID

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_owner(message): return
    text = "🤖 **Sandbox AI Cloud Aktif!**\n\nKirimkan pesan teks atau lampiran file (.apk, .txt, .smali, .py) untuk dianalisis."
    bot.reply_to(message, text, parse_mode='Markdown')

# --- PERBAIKAN TOTAL: DOWNLOAD DOKUMEN VIA JALUR RESMI TELEBOT ---
@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not is_owner(message): return
    
    sent_msg = bot.reply_to(message, "📥 Sedang memproses file dari Telegram...")
    
    try:
        # Ambil informasi berkas dari Telegram
        file_info = bot.get_file(message.document.file_id)
        
        bot.edit_message_text("💾 Mengunduh biner secara aman ke server sandbox...", message.chat.id, sent_msg.message_id)
        
        # Jalur resmi download_file bawaan pyTelegramBotAPI (Anti-Gagal URL)
        downloaded_file = bot.download_file(file_info.file_path)
        
        local_filename = message.document.file_name
        with open(local_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.edit_message_text("🧠 Mengunggah biner ke Sandbox Gemini AI...", message.chat.id, sent_msg.message_id)
        
        # Mengunggah berkas ke Gemini File Storage
        gemini_file = ai_client.files.upload(
            file=local_filename,
            config=types.UploadFileConfig(display_name=local_filename)
        )
        
        bot.edit_message_text("⚡ Gemini sedang membedah kode biner aplikasi Anda...", message.chat.id, sent_msg.message_id)
        
        # Membaca takarir pengguna jika ada
        user_instruction = message.caption if message.caption else "Bedah fungsionalitas kodenya."
        
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[gemini_file, f"Lakukan reverse engineering pada file biner {local_filename} ini. Fokus pada instruksi pengguna berikut: {user_instruction}"],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.2)
        )
        
        # Kirimkan teks laporan akhir tanpa parse_mode agar karakter biner dari AI tidak merusak layout chat
        bot.edit_message_text(response.text, message.chat.id, sent_msg.message_id)
        
        # Hapus berkas setelah selesai diproses agar server tetap bersih
        if os.path.exists(local_filename):
            os.remove(local_filename)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Gagal memproses file. Error: {str(e)}", message.chat.id, sent_msg.message_id)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if not is_owner(message): return
    sent_msg = bot.reply_to(message, "🧠 Memproses analisis teks...")
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.2)
        )
        bot.edit_message_text(response.text, message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    print("Bot Telegram berjalan di Cloud...")
    bot.infinity_polling()
