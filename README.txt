SISTEM NOTA - CV SUBUR ANUGERAH SEJAHTERA
=========================================

Aplikasi web lokal untuk membuat, menyimpan, dan mencetak nota penyaluran
pupuk bersubsidi. Ringan, dirancang untuk PC spek rendah (2 GB RAM).

SYARAT
------
- Windows (termasuk Windows 7)
- Python 3.9 terpasang.
  Unduh: https://www.python.org/downloads/release/python-3913/
  Saat memasang, centang "Add Python to PATH".

CARA PAKAI (sekali saja)
------------------------
1. Klik dua kali  install.bat
   (membuat folder .venv dan memasang Flask + waitress; butuh internet)

MENJALANKAN
-----------
2. Klik dua kali  start.bat
   Browser akan terbuka otomatis ke http://127.0.0.1:5000/
   Biarkan jendela hitam (Command Prompt) tetap terbuka selama memakai aplikasi.
   Untuk berhenti: tutup jendela hitam tersebut.

MENU
----
- Buat Nota      : input Tanggal, Nomor SO, Kuantum; pilih pupuk/PPTS/ekspeditur.
- Riwayat Nota   : cari, cetak ulang, atau cetak beberapa nota sekaligus (2/halaman).
- Jenis Pupuk    : kelola pupuk & harga (UREA, NPK, dst.).
- PPTS / Kios    : kelola kios, kecamatan, penanda tangan.
- Ekspeditur     : kelola ekspeditur & nomor polisi.
- Pengaturan     : identitas perusahaan & teks tetap nota.

DATA
----
Semua data tersimpan di file  data\nota.db  (SQLite).
Untuk cadangan, cukup salin file tersebut.

MENCETAK
--------
Di halaman cetak, klik tombol "Cetak" lalu pilih kertas A4.
Dua nota tercetak per halaman.
