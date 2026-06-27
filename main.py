import os
import telebot
import zipfile  # Digunakan untuk membaca struktur berkas di dalam APK
from groq import Groq  # Pustaka untuk menghubungkan ke Groq Cloud

# 1. Konfigurasi Kunci Akses (Gunakan Environment Variables)
TELEGRAM_TOKEN = "8607503824:AAHq5S9uXD0-6YwxD5zrpmGRBOKADDcNiBQ"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ID Pemilik Bot Anda
OWNER_CHAT_ID = 1209820269  

# 2. Inisialisasi Pustaka
bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_INSTRUCTION = """
Anda adalah asisten AI Sandbox untuk Reverse Engineering. Tugas Anda adalah menganalisis file, kode, 
atau manifes yang dikirimkan. Bedah struktur logika, algoritma, atau indikasi malware jika ada secara objektif.
"""

def is_owner(message):
    return message.chat.id == OWNER_CHAT_ID

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_owner(message): return
    text = "🤖 **Sandbox AI Cloud Aktif (Didukung oleh Groq Llama)!**\n\nKirimkan pesan teks atau lampiran file (.apk, .txt, .smali, .py) untuk dianalisis."
    bot.reply_to(message, text, parse_mode='Markdown')

# --- HANDLER DOKUMEN ANTI-CRASH ---
@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not is_owner(message): return
    
    sent_msg = bot.reply_to(message, "📥 Sedang memproses file dari Telegram...")
    local_filename = message.document.file_name
    
    try:
        # 1. Ambil informasi berkas dari Telegram
        file_info = bot.get_file(message.document.file_id)
        bot.edit_message_text("💾 Mengunduh file secara aman ke server sandbox...", message.chat.id, sent_msg.message_id)
        
        downloaded_file = bot.download_file(file_info.file_path)
        with open(local_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # PERBAIKAN: Cara mengambil string ekstensi file yang benar dari tuple
        file_extension = os.path.splitext(local_filename)[1].lower()
        user_instruction = message.caption if message.caption else "Analisis struktur dan potensi kerentanan berkas ini."
        
        # JIKA FILE ADALAH APK
        if file_extension == '.apk':
            bot.edit_message_text("📦 Mendekompilasi struktur berkas APK Anda...", message.chat.id, sent_msg.message_id)
            
            try:
                with zipfile.ZipFile(local_filename, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                
                # Format daftar isi ZIP menjadi teks murni string
                apk_structure_text = f"Analisis Struktur APK: {local_filename}\n\nDaftar file internal:\n" + "\n".join(file_list[:100])
                if len(file_list) > 100:
                    apk_structure_text += f"\n... dan {len(file_list) - 100} file lainnya."
                
                bot.edit_message_text("⚡ Groq Llama sedang membedah arsitektur APK Anda...", message.chat.id, sent_msg.message_id)
                
                # PERBAIKAN: Mengirim teks gabungan string yang valid ke Groq
                response = ai_client.chat.completions.create(
                    model='llama-3.3-70b-versatile',
                    messages=[
                        {"role": "system", "content": SYSTEM_INSTRUCTION},
                        {"role": "user", "content": f"{apk_structure_text}\n\nInstruksi tambahan user: {user_instruction}"}
                    ],
                    temperature=0.2
                )
                bot.edit_message_text(response.choices.message.content, message.chat.id, sent_msg.message_id)
                
            except zipfile.BadZipFile:
                bot.edit_message_text("❌ File APK rusak atau tidak valid sebagai arsip ZIP.", message.chat.id, sent_msg.message_id)
                
        # JIKA FILE ADALAH TEKS/KODE (TXT, PY, SMALI, DLL)
        else:
            bot.edit_message_text("🧠 Membaca file kode sumber Anda...", message.chat.id, sent_msg.message_id)
            
            with open(local_filename, 'r', encoding='utf-8', errors='ignore') as f:
                code_content = f.read()
            
            bot.edit_message_text("⚡ Groq Llama sedang membedah kode program Anda...", message.chat.id, sent_msg.message_id)
            
            response = ai_client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": f"Nama File: {local_filename}\n\nIsi Kode:\n{code_content}\n\nInstruksi Tambahan: {user_instruction}"}
                ],
                temperature=0.2
            )
            bot.edit_message_text(response.choices.message.content, message.chat.id, sent_msg.message_id)
            
    except Exception as e:
        # Jika ada error, bot tidak akan macet melainkan menginfokan jenis errornya di chat
        bot.edit_message_text(f"❌ Gagal memproses file. Detail Error: {str(e)}", message.chat.id, sent_msg.message_id)
        
    finally:
        # Bersihkan file dari server lokal setelah selesai diproses agar hemat penyimpanan
        if os.path.exists(local_filename):
            os.remove(local_filename)

# --- HANDLER PESAN TEKS VIA GROQ ---
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if not is_owner(message): return
    sent_msg = bot.reply_to(message, "🧠 Memproses analisis teks via Groq...")
    try:
        response = ai_client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": message.text}
            ],
            temperature=0.2
        )
        bot.edit_message_text(response.choices.message.content, message.chat.id, sent_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error API Groq: {str(e)}", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    print("Bot Telegram berjalan...")
    bot.polling(non_stop=True)
