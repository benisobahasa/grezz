# Grezz — GEO (Generative Engine Optimization) Scanner

Cek seberapa siap sebuah website ditemukan & dikutip oleh AI search engine
(ChatGPT, Gemini, Perplexity, AI Overviews), lengkap dengan desain futuristik,
animasi, fitur AI interaktif, dan slot iklan siap monetisasi.

## Yang Baru di Versi Ini

**Aplikasi sekarang full Bahasa Inggris** — semua teks UI, pesan error, dan output AI
(ringkasan, rewrite, chat, FAQ) sekarang berbahasa Inggris, cocok untuk audiens global.

**Animasi tambahan:**
- Cursor glow, scroll-reveal (IntersectionObserver), loading status bergilir, skeleton
  shimmer, tilt-hover di semua card, mobile hamburger menu, FAQ accordion (dari versi
  sebelumnya) — plus baris "trust badges" beranimasi pulse di hero
- Sticky ad bar muncul halus setelah user scroll (bukan langsung muncul di awal), dan
  bisa ditutup — dirancang non-intrusive

**AI dimaksimalkan lebih jauh:**
- Ringkasan konsultatif, AI Rewrite title/meta, chat "Ask Grezz AI" (dari sebelumnya)
- **Baru: AI FAQ Generator** — kalau halaman belum punya FAQPage schema, Gemini membuat
  draf pasangan tanya-jawab berdasarkan konten asli halaman, siap dipakai user untuk
  menambah FAQPage schema mereka sendiri (langsung menutup salah satu rule GEO yang paling
  berbobot)

**Slot iklan lebih banyak, tetap non-intrusive** — sekarang 6 slot: Header, Sidebar,
In-Content, **Native** (baru — disisipkan halus di antara kartu rekomendasi ke-3),
Footer, dan **Sticky Bottom Bar** (baru — kecil, baru muncul setelah scroll, gampang
ditutup, tidak menghalangi konten utama).

**Package lebih lengkap** — ditambahkan `.gitignore` (supaya `.env` dan `venv/` tidak
ikut ke-push ke GitHub) dan `passenger_wsgi.py` (dari revisi sebelumnya) untuk deploy
langsung ke cPanel/Rumahweb.

## Struktur

```
grezz-app/
├── app/
│   ├── main.py               # FastAPI routes + security headers + rate limiting
│   ├── config.py
│   ├── security.py           # proteksi SSRF + rate limiter
│   ├── scraper.py
│   ├── rule_engine.py
│   ├── scoring.py
│   ├── priority_engine.py
│   ├── gemini_client.py      # ringkasan AI, AI rewrite title/meta, chat Q&A
│   ├── cache.py
│   ├── templates/
│   │   ├── base.html         # navbar+logo+mobile menu, cursor glow, cookie consent
│   │   ├── index.html        # hero, FAQ, skeleton loading, scroll-reveal
│   │   ├── privacy.html
│   │   ├── terms.html
│   │   └── partials/
│   │       ├── results.html
│   │       ├── chat_message.html
│   │       ├── error.html
│   │       └── ad_slot.html
│   └── static/
│       ├── css/style.css
│       ├── js/main.js
│       └── img/               # grezz-logo.png & grezz-icon.png
├── deploy/
│   ├── grezz.service          # template systemd
│   └── grezz-nginx.conf       # template Nginx reverse proxy
├── requirements.txt
├── runtime.txt
├── Procfile                    # tetap ada untuk opsi deploy PaaS lain
└── .env.example
```

---

# Panduan Deploy: VS Code → Live di grezz.speakmi.com (cPanel/Rumahweb)

Panduan ini untuk **cPanel shared hosting** (seperti Rumahweb) memakai fitur
**"Setup Python App"** bawaan cPanel — bukan VPS. cPanel menjalankan app Python lewat
Phusion Passenger, karena itu ada file `passenger_wsgi.py` di root project yang
menjembatani FastAPI (ASGI) ke Passenger.

## Bagian 1 — Uji di Lokal (VS Code) — kalau sudah, lewati ke Bagian 2

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # isi GEMINI_API_KEY
uvicorn app.main:app --reload
```
Buka `http://localhost:8000`, pastikan semua fitur jalan normal.

## Bagian 2 — Push ke GitHub

```bash
git init
git add .
git commit -m "Grezz - siap deploy cPanel"
git remote add origin https://github.com/username/grezz-app.git
git branch -M main
git push -u origin main
```
(Kalau repo GitHub sudah ada dari sebelumnya, cukup `git add . && git commit -m "update" && git push`.)

## Bagian 3 — Buat Subdomain di cPanel

1. Login cPanel Rumahweb kamu
2. Cari menu **Subdomains** (biasanya di bagian "Domains")
3. Buat subdomain baru: `grezz` → otomatis jadi `grezz.speakmi.com`
4. Document root boleh dibiarkan default (nanti "Setup Python App" yang akan
   mengatur ulang otomatis) — klik **Create**

## Bagian 4 — Setup Python App

1. Di cPanel, cari menu **Setup Python App** (kadang namanya "Python Selector" —
   biasanya di bagian "Software")
2. Klik **Create Application**, isi:
   - **Python version**: pilih yang tertinggi tersedia (idealnya 3.11, minimal 3.10)
   - **Application root**: nama folder, misalnya `grezz-app` (ini folder tempat
     kode kamu akan berada, relatif dari home directory)
   - **Application URL**: pilih domain `speakmi.com` lalu di kolom di sebelahnya
     ketik `grezz` sehingga jadi `grezz.speakmi.com`
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`
3. Klik **Create**. cPanel akan otomatis membuat folder + virtual environment
   Python kosong, dan menampilkan sebuah baris perintah "Enter to the virtual
   environment" — **copy perintah itu**, akan dipakai di Bagian 6.

## Bagian 5 — Masukkan Kode ke Server

**Opsi A — Git (kalau cPanel kamu punya menu "Git Version Control"):**
1. Menu **Git Version Control** → **Create**
2. Clone URL: `https://github.com/username/grezz-app.git`
3. Repository Path: isi sama persis dengan "Application root" di Bagian 4
   (mis. `grezz-app`)
4. Klik **Create**

**Opsi B — Upload manual (kalau tidak ada Git Version Control):**
1. Di lokal (VS Code terminal), zip project: `zip -r grezz-deploy.zip . -x "venv/*" ".git/*"`
2. cPanel → **File Manager** → masuk ke folder Application root (mis. `grezz-app`)
3. **Upload** → pilih `grezz-deploy.zip` → setelah selesai, klik kanan file → **Extract**

## Bagian 6 — Install Dependencies

1. Buka **Terminal** di cPanel (menu "Advanced" → "Terminal") — kalau Rumahweb
   tidak menyediakan Terminal, lewati ke langkah alternatif di bawah
2. Tempel perintah "activate virtualenv" yang kamu copy di Bagian 4, contoh:
   ```bash
   source /home/USERNAME/virtualenv/grezz-app/3.11/bin/activate && cd ~/grezz-app
   ```
3. Lalu install:
   ```bash
   pip install -r requirements.txt
   ```
   Tunggu sampai selesai (tanpa error merah di akhir).

**Alternatif tanpa Terminal:** buka lagi menu **Setup Python App**, klik nama
aplikasi Grezz kamu, scroll ke bagian bawah — banyak versi cPanel modern
menyediakan kolom untuk paste isi `requirements.txt` atau tombol **"Run Pip
Install"** langsung dari situ tanpa perlu Terminal.

## Bagian 7 — Environment Variables

Masih di halaman **Setup Python App** → buka aplikasi Grezz kamu → cari bagian
**Environment variables**. Tambahkan satu per satu:
```
GEMINI_API_KEY = isi-api-key-kamu
GEMINI_MODEL = gemini-flash-latest
CACHE_TTL_SECONDS = 3600
ADS_ENABLED = false
```
(Iklan diaktifkan belakangan setelah AdSense disetujui — lihat bagian bawah.)
Klik **Save**.

## Bagian 8 — Restart & Tes

1. Di halaman Setup Python App, klik tombol **Restart**
2. Buka `http://grezz.speakmi.com` (masih HTTP dulu) — coba scan website, pastikan
   animasi, logo, dan hasil analisis muncul normal
3. Kalau muncul error 500, cek log: biasanya ada link **"stderr.log"** di halaman
   Setup Python App, atau lewat File Manager di folder aplikasi cari file log

## Bagian 9 — Aktifkan HTTPS

1. cPanel → menu **SSL/TLS Status** (atau **SSL/TLS**)
2. Cari `grezz.speakmi.com` di daftar domain, centang, klik **Run AutoSSL**
   (gratis, otomatis pakai Let's Encrypt/Sectigo tergantung provider)
3. Tunggu beberapa menit, lalu akses `https://grezz.speakmi.com` — harus muncul
   gembok aman

## Update Kode di Masa Depan

**Kalau pakai Git Version Control:** cPanel → Git Version Control → pilih repo
Grezz → **Manage** → **Pull or Deploy** → **Update from Remote**, lalu kalau ada
dependency baru ulangi Bagian 6, lalu **Restart** di Setup Python App.

**Kalau upload manual:** ulangi Bagian 5 Opsi B (timpa file yang berubah), lalu
**Restart**.

## Troubleshooting Cepat

| Gejala | Cek |
|---|---|
| 500 Internal Server Error | Buka file log error di Setup Python App / File Manager, biasanya menunjukkan baris kode yang error |
| "No module named app" | Pastikan struktur folder di server sama persis: `passenger_wsgi.py` sejajar dengan folder `app/`, bukan di dalamnya |
| ModuleNotFoundError untuk suatu package | Ulangi Bagian 6 — pastikan `pip install` dijalankan di dalam virtualenv yang benar (baris `source .../activate` harus sukses dulu) |
| Ganti kode tidak muncul | Pastikan sudah restart app di Setup Python App setelah update kode |
| Domain belum bisa diakses sama sekali | Cek subdomain sudah dibuat di Bagian 3, tunggu beberapa menit untuk propagasi DNS internal cPanel |
| Logo/CSS/JS tidak muncul | Cek folder `app/static/` ikut ter-upload/ter-clone dengan lengkap |

> **Catatan untuk yang punya VPS (bukan shared hosting):** folder `deploy/`
> (`grezz.service` + `grezz-nginx.conf`) masih tersedia di project ini kalau
> suatu saat kamu upgrade ke VPS — tapi untuk cPanel shared hosting, abaikan
> saja folder itu, tidak dipakai.

---

# Alternatif: Deploy ke Koyeb (kalau cPanel tidak support Python)

Kalau paket hosting cPanel kamu ternyata **tidak punya menu "Setup Python App"**
di bagian Software (banyak paket shared hosting murah memang tidak menyediakan
ini), atau kamu sudah kehabisan jatah custom domain gratis di platform lain,
**Koyeb** adalah alternatif solid: ada free tier, deploy langsung dari GitHub,
dan yang penting — **custom domain gratis tanpa batas** di paket gratisnya.

## Bagian 1 — Pastikan Kode Sudah di GitHub

Kalau belum push (atau ada perubahan seperti fix `lxml` di atas):
```bash
git add .
git commit -m "Update requirements, ready for Koyeb"
git push
```

## Bagian 2 — Buat Akun & Service di Koyeb

1. Buka **koyeb.com**, klik **Sign up**, paling gampang pakai **Continue with GitHub**
   (otomatis terhubung ke repo kamu)
2. Di dashboard, klik **Create Service** (atau **Create App**)
3. Pilih deployment method: **GitHub**
4. Kalau diminta authorize, izinkan Koyeb mengakses repo GitHub kamu
5. Pilih repo project Grezz kamu, branch `main`

## Bagian 3 — Konfigurasi Build & Run

Koyeb otomatis mendeteksi ini sebagai app Python lewat `Procfile` yang sudah
ada di project (isinya: `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`).

1. **Builder**: biarkan default (Buildpack) — Koyeb akan otomatis `pip install
   -r requirements.txt` lalu jalankan perintah dari `Procfile`
2. Kalau ada kolom **Run command** yang kosong/perlu diisi manual, isi:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
3. **Port**: pastikan tercantum `8000` (atau biarkan Koyeb baca dari `$PORT`
   otomatis)
4. **Instance type**: pilih yang **Free/Eco**
5. **Region**: pilih yang terdekat (mis. Singapore kalau tersedia)

## Bagian 4 — Environment Variables

Masih di halaman setup, cari bagian **Environment variables**, tambahkan:
```
GEMINI_API_KEY = isi-api-key-kamu
GEMINI_MODEL = gemini-flash-latest
CACHE_TTL_SECONDS = 3600
ADS_ENABLED = false
```

## Bagian 5 — Deploy & Tes

1. Klik **Deploy**
2. Tunggu proses build (tab **Build Logs** akan menampilkan prosesnya —
   pastikan tidak ada error merah seperti kasus `lxml` sebelumnya)
3. Setelah status jadi **Healthy**/hijau, Koyeb kasih URL default, misalnya
   `https://grezz-namakamu.koyeb.app` — buka dan tes scan-nya jalan normal

## Bagian 6 — Pasang Custom Domain

1. Di halaman app kamu di Koyeb, buka tab **Domains**
2. Klik **Add Domain**, ketik `grezz.speakmi.com`
3. Koyeb akan menampilkan target **CNAME** yang perlu kamu daftarkan (bentuknya
   sesuatu seperti `xxxxx.koyeb.app` atau alamat edge Koyeb lainnya) — **copy** nilai itu
4. Buka **cPanel Rumahweb** → cari menu **Zone Editor** (biasanya di bagian
   "Domains") — ini beda dari "Setup Python App", tersedia meski hosting kamu
   tidak support Python
5. Tambah record baru:
   - Type: **CNAME**
   - Name: `grezz`
   - Value/Target: (nilai CNAME dari Koyeb tadi)
   - TTL: default
6. Simpan, lalu kembali ke Koyeb — tunggu beberapa menit sampai statusnya
   berubah jadi **Active** dengan tanda TLS/SSL hijau (Koyeb otomatis
   menerbitkan sertifikat Let's Encrypt setelah DNS terverifikasi)

## Bagian 7 — Tes di Domain Final

Buka `https://grezz.speakmi.com` — harus muncul dengan gembok aman, semua
animasi dan fitur AI jalan normal.

## Update Kode di Masa Depan (Koyeb)

Setiap kali kamu `git push` ke branch `main`, Koyeb otomatis build & deploy
ulang (auto-deploy default menyala). Tidak perlu langkah manual tambahan.

## Troubleshooting Koyeb

| Gejala | Cek |
|---|---|
| Build gagal (mis. lxml/paket lain error compile) | Pastikan versi package di `requirements.txt` tidak dipin terlalu ketat ke versi tanpa prebuilt wheel — longgarkan jadi `>=` seperti yang sudah dilakukan untuk `lxml` |
| App "Unhealthy" terus | Cek **Runtime Logs**, biasanya menunjukkan error Python persis di baris mana |
| Custom domain stuck "Pending" | Cek record CNAME di Zone Editor cPanel sudah persis sama dengan yang diminta Koyeb, tunggu propagasi DNS (bisa sampai 1 jam) |
| 404 / port error | Pastikan `Procfile` memakai `--port $PORT`, bukan port hardcoded seperti `8000` saja |

---

# Alternatif: Deploy ke Vercel (gratis, tanpa kartu kredit)

Vercel paket **Hobby** gratis selamanya, custom domain gratis, dan **tidak perlu kartu kredit sama sekali**. Bedanya dari Render/Koyeb: Vercel menjalankan Python lewat **serverless function** (kode "dibangunkan" per request, bukan server yang terus menyala), jadi butuh file konfigurasi tambahan (`api/index.py` dan `vercel.json`) — keduanya sudah disiapkan di project ini.

**Catatan jujur sebelum mulai:** paket Hobby Vercel secara resmi ditujukan untuk proyek personal/non-komersial. Karena Grezz akan pasang iklan, ini masuk wilayah abu-abu terhadap ToS mereka — penegakan aturannya tidak ketat untuk proyek kecil, tapi tetap ada risiko kecil suatu saat diminta upgrade. Ada juga batas waktu eksekusi per request (di sini sudah diset 60 detik lewat `vercel.json`, cukup untuk hampir semua scan) dan cache/rate-limiter di memori kadang reset karena sifat serverless — bukan masalah besar, cuma bikin cache kurang optimal dibanding Render/Koyeb.

## Bagian 1 — Push Kode ke GitHub

```bash
git add .
git commit -m "Add Vercel deployment config"
git push
```

## Bagian 2 — Daftar & Import Project

1. Buka **vercel.com**, klik **Sign Up**, pilih **Continue with GitHub** (tidak diminta kartu kredit)
2. Di dashboard, klik **Add New** → **Project**
3. Pilih **Import Git Repository**, cari dan pilih repo Grezz kamu
4. Vercel akan mendeteksi `vercel.json` secara otomatis — biarkan **Framework Preset** di posisi **Other**
5. Bagian **Build and Output Settings**: biarkan kosong/default (semua sudah diatur lewat `vercel.json`)

## Bagian 3 — Environment Variables

Sebelum klik Deploy, buka bagian **Environment Variables** di halaman yang sama, tambahkan:
```
GEMINI_API_KEY = isi-api-key-kamu
GEMINI_MODEL = gemini-flash-latest
CACHE_TTL_SECONDS = 3600
ADS_ENABLED = false
```

## Bagian 4 — Deploy

1. Klik **Deploy**
2. Tunggu proses build (biasanya 1-2 menit)
3. Setelah selesai, Vercel kasih URL default seperti `https://grezz-namakamu.vercel.app`
4. Buka URL itu, tes scan sebuah website — pastikan hasil analisis, animasi, dan chat AI-nya jalan

## Bagian 5 — Tambah Custom Domain

1. Di dashboard project, buka tab **Settings** → **Domains**
2. Ketik `grezz.speakmi.com`, klik **Add**
3. Vercel akan menampilkan record yang perlu didaftarkan — karena ini subdomain, biasanya berupa:
   ```
   Type: CNAME
   Name: grezz
   Value: cname.vercel-dns.com
   ```
   (Ikuti persis apa yang ditampilkan Vercel di layar kamu, bisa saja sedikit berbeda)
4. Buka **cPanel Rumahweb** → **Zone Editor** → tambah record **CNAME** sesuai data dari Vercel tadi
5. Kembali ke Vercel, tunggu beberapa menit sampai status domain berubah jadi **Valid Configuration** (centang hijau) — SSL diterbitkan otomatis

## Bagian 6 — Tes Akhir

Buka `https://grezz.speakmi.com` — harus muncul dengan gembok aman dan semua fitur berjalan normal.

## Update Kode di Masa Depan (Vercel)

Setiap `git push` ke `main` otomatis memicu build & deploy baru (auto-deploy default menyala) — tidak ada langkah manual tambahan.

## Troubleshooting Vercel

| Gejala | Cek |
|---|---|
| Build gagal, error "No module named app" | Pastikan `api/index.py` ada di repo dan isinya tidak berubah — dia yang mengarahkan Vercel ke `app.main:app` |
| 500 error / FUNCTION_INVOCATION_FAILED | Buka tab **Logs** di dashboard Vercel, biasanya menunjukkan baris error Python persis |
| Scan lambat/timeout di website tertentu | Wajar untuk website yang responnya lambat — batas 60 detik di `vercel.json` sudah maksimal untuk paket Hobby |
| Static/logo/CSS tidak muncul | Cek `vercel.json` — semua request termasuk `/static/*` diarahkan ke `api/index.py`, yang lalu menyajikan file lewat FastAPI seperti biasa |
| Custom domain stuck "Invalid Configuration" | Cek ulang record CNAME di Zone Editor cPanel persis sama dengan yang diminta Vercel, tunggu propagasi DNS |

---

## Fitur Lengkap

**Bahasa:** UI dan semua output AI dalam Bahasa Inggris.

**AI (Gemini):**
- Ringkasan konsultatif otomatis
- AI Rewrite title & meta description saat bermasalah
- AI FAQ Generator — draf Q&A untuk FAQPage schema berdasarkan konten asli halaman
- Tanya Grezz AI — chat interaktif seputar hasil analisis
- Panel "See How AI Reads Your Page"

**GEO Rule Engine** — 15 rule di 5 kategori: AI Crawlability (robots.txt vs AI bot,
llms.txt, HTTPS), Structured Data (schema Organization/Article/FAQPage, canonical),
Content Clarity (title, meta, H1, kedalaman konten, heading gaya pertanyaan), Trust
Signals (author, tanggal publikasi), Technical Basics.

**Keamanan:** proteksi SSRF (validasi & resolve IP sebelum fetch, tolak IP privat/
internal), rate limiting per IP, batas ukuran unduhan 3MB, security headers
(CSP, HSTS, X-Frame-Options, dll — otomatis menyesuaikan HTTP/HTTPS di belakang proxy).

**Privasi & Iklan:** halaman `/privacy` & `/terms`, cookie consent banner,
`robots.txt` & `sitemap.xml` otomatis, **6 slot iklan** siap AdSense (header, sidebar,
in-content, native, footer, sticky bottom bar) — tampil sebagai placeholder rapi
sampai `ADS_ENABLED=true` dan Slot ID diisi di environment variables.
