"""
Entry point untuk cPanel "Setup Python App" (Phusion Passenger).
Passenger secara default mencari file bernama persis `passenger_wsgi.py` di
root aplikasi, dengan sebuah callable bernama `application`.

Grezz dibangun dengan FastAPI (ASGI), sedangkan Passenger di banyak paket
cPanel shared hosting masih mengharapkan WSGI. a2wsgi menjembatani itu —
membungkus app ASGI kita jadi callable WSGI tanpa mengubah kode FastAPI sama
sekali.

Kalau versi Passenger di hosting kamu ternyata sudah mendukung ASGI langsung,
kamu boleh coba ganti baris `application = ASGIMiddleware(fastapi_app)` di
bawah menjadi `application = fastapi_app` — tapi biarkan default a2wsgi ini
kalau tidak yakin, karena ini yang paling kompatibel di hampir semua cPanel.
"""
import os
import sys

# Pastikan folder project ini ada di path Python, apapun working directory
# yang dipakai Passenger.
sys.path.insert(0, os.path.dirname(__file__))

from a2wsgi import ASGIMiddleware  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402

application = ASGIMiddleware(fastapi_app)
