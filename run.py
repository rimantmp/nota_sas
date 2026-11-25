"""Penjalan aplikasi untuk produksi lokal.

Menggunakan waitress (ringan, jalan di Windows) dan membuka browser otomatis.
Jalankan lewat start.bat.
"""

import threading
import webbrowser

from waitress import serve
from app import app, init_db

HOST = "127.0.0.1"
PORT = 5000
URL = "http://{}:{}/".format(HOST, PORT)


def buka_browser():
    webbrowser.open(URL)


if __name__ == "__main__":
    init_db()
    threading.Timer(1.5, buka_browser).start()
    print("=" * 52)
    print(" Sistem Nota berjalan di: " + URL)
    print(" Biarkan jendela ini terbuka selama memakai aplikasi.")
    print(" Tekan Ctrl+C atau tutup jendela untuk berhenti.")
    print("=" * 52)
    serve(app, host=HOST, port=PORT, threads=4)
