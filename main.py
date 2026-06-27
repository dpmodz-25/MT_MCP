import os
import telebot
import zipfile  # Digunakan untuk membaca manifes dari dalam APK jika dikirim
from google import genai
from google.genai import types
from app import start_server

# Jalankan server Flask paling awal untuk Render
start_server()

# 1. Konfigurasi Kunci Akses (Gunakan API Key Gemini dari Environment Variables)
TELEGRAM_TOKEN = "8607503824:AAEvECrjkQo_GlJQ09_xVtohGMAjbSxOqas"
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

# --- HANDLER DOKUMEN VIA JALUR RESMI TELEBOT + BYPASS APK BLOCK ---
@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not is_owner(message): return
    
    sent_msg = bot.reply_to(message, "📥 Sedang memproses file dari Telegram...")
    
    try:
        # Ambil informasi berkas dari Telegram
        file_info = bot.get_file(message.document.file_id)
        
        bot.edit_message_text("💾 Mengunduh file secara aman ke server sandbox...", message.chat.id, sent_msg.message_id)
        
        # Jalur resmi download_file bawaan pyTelegramBotAPI
        downloaded_file = bot.download_file(file_info.file_path)
        
        local_filename = message.document.file_name
        with open(local_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # PERBAIKAN: Ambil indeks [1] dari tuple untuk mendapatkan string ekstensi file
        file_extension = os.path.splitext(local_filename)[1].lower()
        
        # JIKA FILE ADALAH APK, EKSTRAK STRUKTUR FILE-NYA TERLEBIH DAHULU
        if file_extension == '.apk':
            bot.edit_message_text("📦 Mendekompilasi struktur berkas APK Anda...", message.chat.id, sent_msg.message_id)
            
            try:
                # Membaca daftar isi file di dalam APK (APK adalah file ZIP)
                with zipfile.ZipFile(local_filename, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                
                # Mengubah daftar file menjadi teks agar bisa dianalisis Gemini
                apk_structure_text = f"Analisis Struktur APK: {local_filename}\n\nDaftar file di dalam paket:\n" + "\n".join(file_list[:100])
                if len(file_list) > 100:
                    apk_structure_text += f"\n... dan {len(file_list) - 100} file lainnya."
                
                bot.edit_message_text("⚡ Gemini sedang membedah arsitektur APK Anda...", message.chat.id, sent_msg.message_id)
                
                user_instruction = message.caption if message.caption else "Analisis struktur dan potensi kerentanan aplikasi ini."
                
                response = ai_client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=[apk_structure_text, f"Lakukan reverse engineering pada struktur APK ini. Fokus instruksi: {user_instruction}"],
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.2)
                )
                
                bot.edit_message_text(response.text, message.chat.id, sent_msg.message_id)
                
            except zipfile.BadZipFile:
                bot.edit_message_text("❌ File APK rusak atau tidak valid sebagai arsip ZIP.", message.chat.id, sent_msg.message_id)
                
        # JIKA FILE ADALAH TEKS/KODE (TXT, PY, SMALI, DLL)
        else:
            bot.edit_message_text("🧠 Mengunggah kode sumber ke Sandbox Gemini AI...", message.chat.id, sent_msg.message_id)
            
            gemini_file = ai_client.files.upload(
                file=local_filename,
                config=types.UploadFileConfig(display_name=local_filename, mime_type="text/plain")
            )
            
            bot.edit_message_text("⚡ Gemini sedang membedah kode program Anda...", message.chat.id, sent_msg.message_id)
            
            user_instruction = message.caption if message.caption else "Bedah fungsionalitas kodenya."
            
            response = ai_client.models.generate_content(
                model='gemini-2.0-flash',
                contents=[gemini_file, f"Lakukan reverse engineering pada file teks {local_filename} ini. Fokus pada instruksi pengguna berikut: {user_instruction}"],
                config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.2)
            )
            
            bot.edit_message_text(response.text, message.chat.id, sent_msg.message_id)
            
        # Bersihkan file dari lokal server setelah selesai diproses
        if os.path.exists(local_filename):
            os.remove(local_filename)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Gagal memproses file. Error: {str(e)}", message.chat.id, sent_msg.message_id)
        if 'local_filename' in locals() and os.path.exists(local_filename):
            os.remove(local_filename)

# --- HANDLER PESAN TEKS ---
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if not is_owner(message): return
    sent_msg = bot.reply_to(message, "🧠 Memproses analisis teks...")
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.0-flash',
            contents=message.text,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION, temperature=0.2)
        )
        bot.edit_message_text(response.text, message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    print("Bot Telegram berjalan di Cloud...")
    bot.infinity_polling()
