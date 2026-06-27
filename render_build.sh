#!/usr/bin/env bash
# Keluar jika ada error
set -o errexit

# 1. Unduh dan instal Java Runtime Portabel (OpenJDK 17) secara lokal di folder Render
echo "☕ Mengunduh Java Runtime Portabel untuk Render..."
mkdir -p $HOME/java
curl -sL "https://github.com" | tar -xz -C $HOME/java --strip-components=1

# 2. Masukkan Java ke PATH sistem Render secara permanen
export PATH=$HOME/java/bin:$PATH

# 3. Unduh biner Apktool terbaru dari repositori resmi
echo "📦 Memasang Apktool lokal engine..."
mkdir -p $HOME/bin
curl -sL "https://githubusercontent.com" -o $HOME/bin/apktool
curl -sL "https://github.com" -o $HOME/bin/apktool.jar
chmod +x $HOME/bin/apktool $HOME/bin/apktool.jar

# 4. Instal dependensi Python via pip
pip install -r requirements.txt
