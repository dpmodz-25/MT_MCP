import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types
from pyaxmlparser import APK

# AMBIL KUNCI RAHASIA DARI ENVIRONMENT VARIABLES SERVER (UNTUK KEAMANAN)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    print("❌ ERROR: TELEGRAM_TOKEN atau GEMINI_API_KEY belum di-setting!")
    exit(1)

# Inisialisasi Google GenAI Client
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# --- MODUL FITUR READ-ONLY (MT MANAGER STYLE) ---
def baca_informasi_dasar(apk_path: str) -> str:
    try:
        apk = APK(apk_path)
        detail = f"📦 **Package Name:** {apk.package}\n"
        detail += f"🔢 **Version Name:** {apk.version_name}\n"
        detail += f"🎯 **Version Code:** {apk.version_code}\n"
        
        permissions = apk.permissions
        detail += f"\n🛡️ **Permissions ({len(permissions)} total):**\n"
        detail += "\n".join([f"- {p.split('.')[-1]}" for p in list(permissions)[:10]])
        if len(permissions) > 10: detail += "\n- ... dan lainnya."
        return detail
    except Exception as e: return f"Gagal membaca info APK: {str(e)}"

def deteksi_aktivitas_dan_layanan(apk_path: str) -> str:
    try:
        apk = APK(apk_path)
        # Mengambil komponen dasar utama dari manifes XML
        hasil = f"📱 **Total Activities:** {len(apk.activities)}\n"
        hasil += f"⚙️ **Total Services:** {len(apk.services)}\n"
        hasil += f"📡 **Total Broadcast Receivers:** {len(apk.receivers)}\n\n"
        hasil += "💡 *Catatan:* Komponen berhasil dimuat ke memori sandbox."
        return hasil
    except Exception as e: return f"Gagal membaca komponen: {str(e)}"

def ekstrak_aset_dan_jni(apk_path: str) -> str:
    try:
        apk = APK(apk_path)
        # Menggunakan pustaka zipfile internal bawaan parser untuk membaca daftar file biner
        daftar_file = apk.zip.namelist()
        assets_files = [f for f in daftar_file if f.startswith("assets/")]
        jni_files = [f for f in daftar_file if f.startswith("lib/") and f.endswith(".so")]
                
        hasil = "📂 **Hasil Pemindaian Struktur File Internal:**\n\n"
        hasil += f"🤖 **Native Libraries / JNI ({len(jni_files)}):**\n"
        hasil += "\n".join([f"- `{f}`" for f in jni_files[:15]]) if jni_files else "_Tidak ada .so_\n"
        if len(jni_files) > 15: hasil += f"\n- ...dan {len(jni_files)-15} lainnya."
        
        hasil += f"\n\n📦 **Application Assets ({len(assets_files)}):**\n"
        hasil += "\n".join([f"- `{f}`" for f in assets_files[:15]]) if assets_files else "_Tidak ada assets_\n"
        if len(assets_files) > 15: hasil += f"\n- ...dan {len(assets_files)-15} lainnya."
        return hasil
    except Exception as e: return f"Gagal mengekstraksi: {str(e)}"

# --- DAFTAR ALAT MCP YANG BISA DIPANGGIL GEMINI ---
tools_list = [baca_informasi_dasar, deteksi_aktivitas_dan_layanan, ekstrak_aset_dan_jni]

# --- HANDLERS TELEGRAM ---
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    file_name = update.message.document.file_name
    if not file_name.endswith('.apk'):
        await update.message.reply_text("❌ Kirimkan dokumen berformat `.apk`")
        return
    apk_path = f"./downloads/{file_name}"
    os.makedirs("./downloads", exist_ok=True)
    await update.message.reply_text("📥 Mengunduh APK ke sandbox cloud...")
    await file.download_to_drive(apk_path)
    context.user_data['active_apk'] = apk_path
    await update.message.reply_text(f"✅ `{file_name}` siap! Silakan tanya AI (Contoh: 'Cek folder assets-nya' atau 'Cek info library .so biner')")

async def handle_chat_with_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    apk_path = context.user_data.get('active_apk')
    if not apk_path:
        await update.message.reply_text("⚠️ Kirim file APK terlebih dahulu.")
        return

    config = types.GenerateContentConfig(
        system_instruction="Anda adalah AI Analis APK Read-Only bergaya MT Manager. Gunakan fungsi alat (tools) yang disediakan untuk menjawab setiap pertanyaan pengguna secara mendalam berdasarkan isi biner asli.",
        tools=tools_list,
        temperature=0.3
    )
    
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=user_msg,
        config=config
    )

    if response.function_calls:
        for call in response.function_calls:
            nama_f = call.name
            await update.message.reply_text(f"🔍 [MCP Calling] Memproses fungsi `{nama_f}`...")
            
            if nama_f == "baca_informasi_dasar": hasil = baca_informasi_dasar(apk_path)
            elif nama_f == "deteksi_aktivitas_dan_layanan": hasil = deteksi_aktivitas_dan_layanan(apk_path)
            elif nama_f == "ekstrak_aset_dan_jni": hasil = ekstrak_aset_dan_jni(apk_path)
            else: hasil = "Fungsi tidak ditemukan."
            
            await update.message.reply_text(hasil)
    else:
        await update.message.reply_text(response.text)

if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat_with_ai))
    print("Bot Terhubung dengan Gemini...")
    app.run_polling()
