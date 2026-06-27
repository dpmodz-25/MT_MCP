import os
import telebot
from google import genai
from google.genai import types
from app import start_server

# 1. Pastikan port server Flask berjalan paling awal
if __name__ == "__main__":
    start_server()

# 2. Ambil token dari environment variables Render
TELEGRAM_TOKEN = os.getenv("8607503824:AAGZlV1J0oi0o_NEjllTxjc11E8Jc6cDFd0")
GEMINI_API_KEY = os.getenv("AQ.Ab8RN6JWLV9wcS8Ao-iSSTCLMDiFwZlDrqWdWfyEpC2onC-ANA")
OWNER_CHAT_ID = 123456789  # Pastikan ini sudah diganti dengan Chat ID Anda asli!

# Validasi manual agar bot tidak crash tanpa alasan yang jelas
if not TELEGRAM_TOKEN:
    raise ValueError("Error: TELEGRAM_TOKEN tidak ditemukan di Environment Variables Render!")
if not GEMINI_API_KEY:
    raise ValueError("Error: GEMINI_API_KEY tidak ditemukan di Environment Variables Render!")

# 3. Inisialisasi Bot dan AI Client setelah validasi lolos
bot = telebot.TeleBot(8607503824:AAGZlV1J0oi0o_NEjllTxjc11E8Jc6cDFd0)
ai_client = genai.Client(api_key=AQ.Ab8RN6JWLV9wcS8Ao-iSSTCLMDiFwZlDrqWdWfyEpC2onC-ANA)

SYSTEM_INSTRUCTION = """
Anda adalah asisten AI Sandbox untuk Reverse Engineering. Tugas Anda adalah menganalisis file, kode, 
atau manifes yang dikirimkan. Bedah struktur logika, algoritma, atau indikasi malware jika ada secara objektif.
"""

# ... (Sisa kode di bawahnya seperti 'is_owner', 'handle_document', dsb. tetap sama seperti sebelumnya) ...

# Bagian paling bawah file main.py ubah menjadi hanya ini:
print("Bot Telegram berjalan di Cloud...")
bot.infinity_polling()
