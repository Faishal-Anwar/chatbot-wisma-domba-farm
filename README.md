# Wisma Domba Farm - RAG Chatbot

Chatbot ini menggunakan API Gemini dan teknik Retrieval-Augmented Generation (RAG) untuk memberikan informasi seputar Wisma Domba Farm.

## Fitur
- RAG menggunakan LangChain dan ChromaDB.
- Backend menggunakan FastAPI.
- Frontend menggunakan HTML/CSS/JS (seperti yang diminta).
- Integrasi API Gemini (gemini-1.5-flash).

## Cara Menjalankan

### 1. Persiapan Lingkungan
Pastikan Anda sudah menginstal Python. Kemudian ikuti langkah berikut:

```bash
# Membuat virtual environment (jika belum)
python3 -m venv venv

# Mengaktifkan venv
source venv/bin/activate  # Untuk Linux/macOS
# venv\Scripts\activate   # Untuk Windows

# Instal dependensi
pip install -r requirements.txt
```

### 2. Konfigurasi API Key
Salin file `.env.example` menjadi `.env` dan masukkan API Key Gemini Anda.

```bash
cp .env.example .env
```

Edit file `.env`:
```
GOOGLE_API_KEY=AIzaSy... (masukkan key Anda)
```

### 3. Jalankan Server Backend
```bash
python main.py
```
Server akan berjalan di `http://127.0.0.1:8000`.

### 4. Buka Frontend
Buka file `index.html` di browser Anda. Pastikan server backend sedang berjalan agar chatbot bisa merespon.

## Struktur Folder
- `data/`: Berisi dokumen teks informasi Wisma Domba Farm (Knowledge Base).
- `main.py`: Script backend FastAPI.
- `index.html`: UI Chatbot.
- `vector_db/`: Folder database vektor (otomatis dibuat saat dijalankan).
- `venv/`: Virtual environment.
 
