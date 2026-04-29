# Behance User Search Scraper

Script ini digunakan untuk mengambil data user dari Behance berdasarkan kata kunci pencarian menggunakan Python dan Playwright.

## Prasyarat
- Python 3.8 atau versi lebih baru
- Pip (Python Package Manager)

---

## Panduan Instalasi & Penggunaan (macOS)

### 1. Persiapan Environment
Buka Terminal dan arahkan ke folder project:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalasi Dependensi
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Menjalankan Scraper
```bash
# Contoh: Mencari designer di Indonesia
python3 behance_scraper.py -q "designer" --country ID -n 50 -o results.json
```

---

## Panduan Instalasi & Penggunaan (Windows)

### 1. Persiapan Environment
Buka PowerShell atau Command Prompt dan arahkan ke folder project:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Instalasi Dependensi
```powershell
pip install -r requirements.txt
playwright install chromium
```

### 3. Menjalankan Scraper
```powershell
# Contoh: Mencari photographer
python behance_scraper.py -q "photographer" -n 20 -o results.json
```

---

## Argumen Command Line
| Argumen | Deskripsi | Contoh |
|---------|-----------|--------|
| `-q` | Kata kunci pencarian (Query) | `-q "graphic designer"` |
| `-n` | Jumlah user yang ingin diambil | `-n 100` |
| `-o` | Nama file output JSON | `-o data.json` |
| `--country` | Kode negara (ISO 3166-1 alpha-2) | `--country ID` |

## Hasil Output
Data akan disimpan dalam format JSON dengan informasi meliputi:
- Nama Lengkap & Username
- Lokasi (Kota, Negara)
- URL Profile & Avatar
- Statistik (Project Views, Appreciations, Followers, dll)
- Social Media Links
- Daftar Project
