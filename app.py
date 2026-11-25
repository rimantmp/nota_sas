"""Sistem Nota Penyaluran Pupuk Bersubsidi - CV Subur Anugerah Sejahtera.

Aplikasi web ringan (Flask + SQLite stdlib) untuk membuat, menyimpan, dan
mencetak nota. Dirancang agar hemat memori sehingga nyaman di PC spek rendah.
"""

import os
import secrets
import sqlite3
from datetime import date
from flask import (
    Flask, g, render_template, request, redirect, url_for, flash, abort
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "nota.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

app = Flask(__name__)
# Kunci sesi (hanya untuk pesan notifikasi). Diambil dari variabel lingkungan bila ada,
# selain itu dibuat acak setiap aplikasi dijalankan.
app.config["SECRET_KEY"] = os.environ.get("NOTA_SECRET_KEY") or secrets.token_hex(32)
# Muat ulang template otomatis saat file berubah (tanpa perlu restart server).
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

BULAN_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

SUB_KALTIM = "PENYALURAN PUPUK BERSUBSIDI PT. PUPUK KALIMANTAN TIMUR"
SUB_PETRO = "PENYALURAN PUPUK BERSUBSIDI PT. PETROKIMIA GRESIK"


# --------------------------------------------------------------------------
# Basis data
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Membuat basis data dan mengisi data awal jika belum ada."""
    os.makedirs(DATA_DIR, exist_ok=True)
    first_time = not os.path.exists(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        con.executescript(fh.read())

    # Migrasi: skema lama menyimpan satu kecamatan di tabel ppts.
    cols = [r[1] for r in con.execute("PRAGMA table_info(ppts)")]
    if "kecamatan" in cols:
        for row in con.execute("SELECT id, kecamatan FROM ppts").fetchall():
            if row["kecamatan"]:
                con.execute(
                    "INSERT INTO ppts_kecamatan (ppts_id, nama) VALUES (?, ?)",
                    (row["id"], row["kecamatan"]))
        con.executescript(
            """
            CREATE TABLE ppts_baru (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                penanggung_jawab TEXT NOT NULL,
                aktif INTEGER NOT NULL DEFAULT 1);
            INSERT INTO ppts_baru (id, nama, penanggung_jawab, aktif)
                SELECT id, nama, penanggung_jawab, aktif FROM ppts;
            DROP TABLE ppts;
            ALTER TABLE ppts_baru RENAME TO ppts;
            """)

    # Migrasi: tambah kolom subjudul pada pupuk (subjudul per jenis pupuk).
    pcols = [r[1] for r in con.execute("PRAGMA table_info(pupuk)")]
    if "subjudul" not in pcols:
        con.execute("ALTER TABLE pupuk ADD COLUMN subjudul TEXT NOT NULL DEFAULT ''")
    row = con.execute("SELECT subjudul FROM pengaturan WHERE id = 1").fetchone()
    default_sub = row["subjudul"] if row else ""
    for r in con.execute("SELECT id, nama, subjudul FROM pupuk").fetchall():
        if not (r["subjudul"] or "").strip():
            up = (r["nama"] or "").strip().upper()
            s = SUB_KALTIM if up == "UREA" else SUB_PETRO if up == "NPK" else default_sub
            con.execute("UPDATE pupuk SET subjudul = ? WHERE id = ?", (s, r["id"]))

    cur = con.execute("SELECT COUNT(*) AS n FROM pengaturan")
    if cur.fetchone()["n"] == 0:
        con.execute(
            """INSERT INTO pengaturan
               (id, nama_perusahaan, alamat, kota, judul_dokumen, subjudul,
                nama_pud, label_pud)
               VALUES (1, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "CV SUBUR ANUGERAH SEJAHTERA",
                "Jl. Pembangunan No. 12",
                "RANTEPAO - KAB. TORAJA UTARA",
                "NOTA PELAKU USAHA DISTRIBUSI",
                "PENYALURAN PUPUK BERSUBSIDI PT. PUPUK KALIMANTAN TIMUR",
                "Libertyni Yuella Z. P",
                "CV. Subur Anugerah Sejahtera",
            ),
        )
    if con.execute("SELECT COUNT(*) AS n FROM pupuk").fetchone()["n"] == 0:
        con.executemany(
            "INSERT INTO pupuk (nama, harga_per_ton, subjudul) VALUES (?, ?, ?)",
            [("UREA", 1655760, SUB_KALTIM), ("NPK", 1695760, SUB_PETRO)],
        )
    if con.execute("SELECT COUNT(*) AS n FROM ppts").fetchone()["n"] == 0:
        cur_ppts = con.execute(
            "INSERT INTO ppts (nama, penanggung_jawab) VALUES (?, ?)",
            ("Surya Tani", "Titus Rombo'"))
        con.execute(
            "INSERT INTO ppts_kecamatan (ppts_id, nama) VALUES (?, ?)",
            (cur_ppts.lastrowid, "Mengkendek"))
    if con.execute("SELECT COUNT(*) AS n FROM ekspeditur").fetchone()["n"] == 0:
        con.execute(
            "INSERT INTO ekspeditur (nama, no_pol) VALUES (?, ?)",
            ("David", "DP8179KE"),
        )
    con.commit()
    con.close()
    return first_time


# --------------------------------------------------------------------------
# Helper
# --------------------------------------------------------------------------
def rupiah(nilai):
    try:
        return "{:,}".format(int(round(float(nilai))))
    except (TypeError, ValueError):
        return "0"


app.jinja_env.filters["rupiah"] = rupiah


def tanggal_indonesia(iso):
    """'2026-06-02' -> '02 Juni 2026'. Mengembalikan input apa adanya jika gagal."""
    try:
        th, bl, hr = iso.split("-")
        return "{:02d} {} {}".format(int(hr), BULAN_ID[int(bl)], th)
    except (ValueError, IndexError):
        return iso


def get_pengaturan():
    return get_db().execute("SELECT * FROM pengaturan WHERE id = 1").fetchone()


# --------------------------------------------------------------------------
# Nota
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return redirect(url_for("nota_baru"))


def _kecamatan_map(db):
    """Peta {ppts_id: [nama kecamatan, ...]}."""
    hasil = {}
    for r in db.execute(
            "SELECT ppts_id, nama FROM ppts_kecamatan ORDER BY nama").fetchall():
        hasil.setdefault(r["ppts_id"], []).append(r["nama"])
    return hasil


@app.route("/nota/baru", methods=["GET", "POST"])
def nota_baru():
    db = get_db()
    daftar_pupuk = db.execute(
        "SELECT * FROM pupuk WHERE aktif = 1 ORDER BY nama").fetchall()
    daftar_ppts = db.execute(
        "SELECT * FROM ppts WHERE aktif = 1 ORDER BY nama").fetchall()
    daftar_eksp = db.execute(
        "SELECT * FROM ekspeditur WHERE aktif = 1 ORDER BY nama").fetchall()
    kecamatan_map = _kecamatan_map(db)
    pupuk_by_id = {p["id"]: p for p in daftar_pupuk}
    hari_ini = date.today().isoformat()

    def render_form(baris, shared):
        return render_template(
            "nota_baru.html", daftar_pupuk=daftar_pupuk,
            daftar_ppts=daftar_ppts, daftar_eksp=daftar_eksp,
            kecamatan_map=kecamatan_map, hari_ini=hari_ini,
            baris=baris, shared=shared)

    if request.method == "POST":
        shared = {
            "ppts_id": request.form.get("ppts_id", ""),
            "ekspeditur_id": request.form.get("ekspeditur_id", ""),
            "kecamatan": request.form.get("kecamatan", "").strip(),
        }
        tgl_list = request.form.getlist("tanggal")
        so_list = request.form.getlist("nomor_so")
        pid_list = request.form.getlist("pupuk_id")
        qty_list = request.form.getlist("kuantum")
        n = max(len(tgl_list), len(so_list), len(pid_list), len(qty_list), 0)

        baris = []
        for i in range(n):
            baris.append({
                "tanggal": tgl_list[i] if i < len(tgl_list) else "",
                "nomor_so": (so_list[i] if i < len(so_list) else "").strip(),
                "pupuk_id": pid_list[i] if i < len(pid_list) else "",
                "kuantum": (qty_list[i] if i < len(qty_list) else "").strip(),
            })

        errors = []
        ppts = db.execute(
            "SELECT * FROM ppts WHERE id = ?", (shared["ppts_id"],)).fetchone()
        eksp = db.execute(
            "SELECT * FROM ekspeditur WHERE id = ?", (shared["ekspeditur_id"],)).fetchone()
        if ppts is None:
            errors.append("PPTS belum dipilih.")
        if eksp is None:
            errors.append("Ekspeditur belum dipilih.")
        if ppts is not None:
            valid_kec = kecamatan_map.get(ppts["id"], [])
            if not shared["kecamatan"]:
                errors.append("Kecamatan belum dipilih.")
            elif shared["kecamatan"] not in valid_kec:
                errors.append("Kecamatan tidak sesuai dengan PPTS terpilih.")

        valid_rows = []
        for idx, r in enumerate(baris, 1):
            if not (r["nomor_so"] or r["kuantum"]):
                continue  # abaikan baris tanpa isi (tanggal default saja diabaikan)
            kurang = []
            if not r["tanggal"]:
                kurang.append("tanggal")
            if not r["nomor_so"]:
                kurang.append("nomor SO")
            try:
                kuan = float(r["kuantum"])
                if kuan <= 0:
                    kurang.append("kuantum")
            except ValueError:
                kuan = 0
                kurang.append("kuantum")
            pupuk = pupuk_by_id.get(int(r["pupuk_id"])) if r["pupuk_id"].isdigit() else None
            if pupuk is None:
                kurang.append("pupuk")
            if kurang:
                errors.append("Baris %d: lengkapi %s." % (idx, ", ".join(kurang)))
            else:
                valid_rows.append((r, pupuk, kuan))

        if not errors and not valid_rows:
            errors.append("Isi minimal satu baris nota.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_form(baris, shared)

        p = get_pengaturan()
        ids = []
        for (r, pupuk, kuan) in valid_rows:
            jumlah = int(round(kuan * pupuk["harga_per_ton"]))
            cur = db.execute(
                """INSERT INTO nota
                   (tanggal_iso, tanggal_tampil, nomor_so, kuantum,
                    pupuk_nama, harga_per_ton, jumlah,
                    ppts_nama, kecamatan, ppts_penandatangan,
                    ekspeditur_nama, no_pol,
                    nama_perusahaan, alamat, kota, judul_dokumen, subjudul,
                    nama_pud, label_pud)
                   VALUES (?,?,?,?, ?,?,?, ?,?,?, ?,?, ?,?,?,?,?, ?,?)""",
                (r["tanggal"], tanggal_indonesia(r["tanggal"]), r["nomor_so"], kuan,
                 pupuk["nama"], pupuk["harga_per_ton"], jumlah,
                 ppts["nama"], shared["kecamatan"], ppts["penanggung_jawab"],
                 eksp["nama"], eksp["no_pol"],
                 p["nama_perusahaan"], p["alamat"], p["kota"],
                 p["judul_dokumen"], pupuk["subjudul"], p["nama_pud"], p["label_pud"]),
            )
            ids.append(cur.lastrowid)
        db.commit()
        flash("%d nota berhasil disimpan." % len(ids), "sukses")
        return redirect(url_for("nota_cetak", ids=",".join(str(i) for i in ids)))

    pid0 = daftar_pupuk[0]["id"] if daftar_pupuk else ""
    baris = [{"tanggal": hari_ini, "nomor_so": "", "pupuk_id": pid0, "kuantum": ""}]
    return render_form(baris, {})


@app.route("/nota")
def nota_riwayat():
    db = get_db()
    q = request.args.get("q", "").strip()
    dari = request.args.get("dari", "").strip()
    sampai = request.args.get("sampai", "").strip()

    clauses, params = [], []
    if q:
        like = "%" + q + "%"
        clauses.append("(nomor_so LIKE ? OR ppts_nama LIKE ? OR pupuk_nama LIKE ?)")
        params += [like, like, like]
    if dari:
        clauses.append("tanggal_iso >= ?")
        params.append(dari)
    if sampai:
        clauses.append("tanggal_iso <= ?")
        params.append(sampai)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = db.execute(
        "SELECT * FROM nota" + where + " ORDER BY tanggal_iso DESC, id DESC",
        params).fetchall()
    total_jumlah = sum(r["jumlah"] for r in rows)
    return render_template("nota_riwayat.html", notas=rows, q=q, dari=dari,
                           sampai=sampai, total_jumlah=total_jumlah)


@app.route("/nota/cetak")
def nota_cetak():
    ids_raw = request.args.get("ids", "")
    ids = [i for i in ids_raw.split(",") if i.strip().isdigit()]
    if not ids:
        abort(404)
    db = get_db()
    placeholders = ",".join("?" for _ in ids)
    rows = db.execute(
        "SELECT * FROM nota WHERE id IN ({}) ORDER BY tanggal_iso, id".format(
            placeholders), ids).fetchall()
    if not rows:
        abort(404)
    return render_template("nota_cetak.html", notas=rows)


@app.route("/nota/<int:nota_id>/hapus", methods=["POST"])
def nota_hapus(nota_id):
    db = get_db()
    db.execute("DELETE FROM nota WHERE id = ?", (nota_id,))
    db.commit()
    flash("Nota dihapus.", "sukses")
    return redirect(url_for("nota_riwayat"))


# --------------------------------------------------------------------------
# Master: Pupuk
# --------------------------------------------------------------------------
@app.route("/pupuk")
def pupuk_list():
    rows = get_db().execute("SELECT * FROM pupuk ORDER BY nama").fetchall()
    return render_template("pupuk.html", rows=rows)


@app.route("/pupuk/simpan", methods=["POST"])
def pupuk_simpan():
    db = get_db()
    pid = request.form.get("id", "").strip()
    nama = request.form.get("nama", "").strip()
    subjudul = request.form.get("subjudul", "").strip()
    harga_raw = request.form.get("harga_per_ton", "").replace(".", "").replace(",", "").strip()
    try:
        harga = int(harga_raw)
    except ValueError:
        harga = -1
    if not nama or harga < 0:
        flash("Nama dan harga (angka) wajib diisi.", "error")
        return redirect(url_for("pupuk_list"))
    if not subjudul:
        p = get_pengaturan()
        subjudul = p["subjudul"] if p else ""
    if pid.isdigit():
        db.execute("UPDATE pupuk SET nama = ?, harga_per_ton = ?, subjudul = ? WHERE id = ?",
                   (nama, harga, subjudul, pid))
        flash("Data pupuk diperbarui.", "sukses")
    else:
        db.execute("INSERT INTO pupuk (nama, harga_per_ton, subjudul) VALUES (?, ?, ?)",
                   (nama, harga, subjudul))
        flash("Pupuk ditambahkan.", "sukses")
    db.commit()
    return redirect(url_for("pupuk_list"))


@app.route("/pupuk/<int:pid>/hapus", methods=["POST"])
def pupuk_hapus(pid):
    db = get_db()
    db.execute("DELETE FROM pupuk WHERE id = ?", (pid,))
    db.commit()
    flash("Pupuk dihapus.", "sukses")
    return redirect(url_for("pupuk_list"))


# --------------------------------------------------------------------------
# Master: PPTS
# --------------------------------------------------------------------------
@app.route("/ppts")
def ppts_list():
    db = get_db()
    rows = db.execute("SELECT * FROM ppts ORDER BY nama").fetchall()
    kec = {}
    for k in db.execute(
            "SELECT id, ppts_id, nama FROM ppts_kecamatan ORDER BY nama").fetchall():
        kec.setdefault(k["ppts_id"], []).append(k)
    return render_template("ppts.html", rows=rows, kec=kec)


def _bersihkan_kecamatan(daftar):
    """Rapikan daftar kecamatan: buang yang kosong dan duplikat (tanpa membedakan huruf besar/kecil)."""
    hasil, sudah = [], set()
    for k in daftar:
        k = " ".join(k.split())
        if k and k.lower() not in sudah:
            sudah.add(k.lower())
            hasil.append(k)
    return hasil


@app.route("/ppts/baru")
def ppts_baru():
    return render_template("ppts_form.html", ppts=None, kecamatan=[],
                           nama="", pj="")


@app.route("/ppts/<int:pid>/ubah")
def ppts_ubah(pid):
    db = get_db()
    row = db.execute("SELECT * FROM ppts WHERE id = ?", (pid,)).fetchone()
    if row is None:
        abort(404)
    kec = [k["nama"] for k in db.execute(
        "SELECT nama FROM ppts_kecamatan WHERE ppts_id = ? ORDER BY nama", (pid,))]
    return render_template("ppts_form.html", ppts=row, kecamatan=kec,
                           nama=row["nama"], pj=row["penanggung_jawab"])


@app.route("/ppts/simpan", methods=["POST"])
def ppts_simpan():
    db = get_db()
    pid = request.form.get("id", "").strip()
    nama = " ".join(request.form.get("nama", "").split())
    pj = " ".join(request.form.get("penanggung_jawab", "").split())
    kecamatan = _bersihkan_kecamatan(request.form.getlist("kecamatan"))

    errors = []
    if not nama:
        errors.append("Nama kios wajib diisi.")
    if not pj:
        errors.append("Nama penanda tangan wajib diisi.")
    if not kecamatan:
        errors.append("Isi minimal satu kecamatan yang dilayani kios ini.")
    if errors:
        for e in errors:
            flash(e, "error")
        row = db.execute("SELECT * FROM ppts WHERE id = ?", (pid,)).fetchone() if pid.isdigit() else None
        return render_template("ppts_form.html", ppts=row, kecamatan=kecamatan,
                               nama=nama, pj=pj)

    if pid.isdigit():
        db.execute("UPDATE ppts SET nama=?, penanggung_jawab=? WHERE id=?",
                   (nama, pj, pid))
        ppts_id = int(pid)
        pesan = "Kios %s diperbarui." % nama
    else:
        ppts_id = db.execute("INSERT INTO ppts (nama, penanggung_jawab) VALUES (?, ?)",
                             (nama, pj)).lastrowid
        pesan = "Kios %s ditambahkan." % nama
    # Nota menyimpan salinan nama kecamatan, jadi mengganti daftar ini aman.
    db.execute("DELETE FROM ppts_kecamatan WHERE ppts_id = ?", (ppts_id,))
    db.executemany("INSERT INTO ppts_kecamatan (ppts_id, nama) VALUES (?, ?)",
                   [(ppts_id, k) for k in kecamatan])
    db.commit()
    flash(pesan, "sukses")
    return redirect(url_for("ppts_list"))


@app.route("/ppts/<int:pid>/kecamatan/tambah", methods=["POST"])
def ppts_kecamatan_tambah(pid):
    db = get_db()
    nama = request.form.get("nama", "").strip()
    if not nama:
        flash("Nama kecamatan wajib diisi.", "error")
    else:
        db.execute("INSERT INTO ppts_kecamatan (ppts_id, nama) VALUES (?, ?)",
                   (pid, nama))
        db.commit()
        flash("Kecamatan ditambahkan.", "sukses")
    return redirect(url_for("ppts_list"))


@app.route("/ppts/kecamatan/<int:kid>/hapus", methods=["POST"])
def ppts_kecamatan_hapus(kid):
    db = get_db()
    db.execute("DELETE FROM ppts_kecamatan WHERE id = ?", (kid,))
    db.commit()
    flash("Kecamatan dihapus.", "sukses")
    return redirect(url_for("ppts_list"))


@app.route("/ppts/<int:pid>/hapus", methods=["POST"])
def ppts_hapus(pid):
    db = get_db()
    row = db.execute("SELECT nama FROM ppts WHERE id = ?", (pid,)).fetchone()
    db.execute("DELETE FROM ppts WHERE id = ?", (pid,))
    db.commit()
    flash("Kios %s dihapus." % (row["nama"] if row else ""), "sukses")
    return redirect(url_for("ppts_list"))


# --------------------------------------------------------------------------
# Master: Ekspeditur
# --------------------------------------------------------------------------
@app.route("/ekspeditur")
def ekspeditur_list():
    rows = get_db().execute("SELECT * FROM ekspeditur ORDER BY nama").fetchall()
    return render_template("ekspeditur.html", rows=rows)


@app.route("/ekspeditur/simpan", methods=["POST"])
def ekspeditur_simpan():
    db = get_db()
    eid = request.form.get("id", "").strip()
    nama = request.form.get("nama", "").strip()
    no_pol = request.form.get("no_pol", "").strip()
    if not (nama and no_pol):
        flash("Nama dan nomor polisi wajib diisi.", "error")
        return redirect(url_for("ekspeditur_list"))
    if eid.isdigit():
        db.execute("UPDATE ekspeditur SET nama=?, no_pol=? WHERE id=?",
                   (nama, no_pol, eid))
        flash("Data ekspeditur diperbarui.", "sukses")
    else:
        db.execute("INSERT INTO ekspeditur (nama, no_pol) VALUES (?, ?)",
                   (nama, no_pol))
        flash("Ekspeditur ditambahkan.", "sukses")
    db.commit()
    return redirect(url_for("ekspeditur_list"))


@app.route("/ekspeditur/<int:eid>/hapus", methods=["POST"])
def ekspeditur_hapus(eid):
    db = get_db()
    db.execute("DELETE FROM ekspeditur WHERE id = ?", (eid,))
    db.commit()
    flash("Ekspeditur dihapus.", "sukses")
    return redirect(url_for("ekspeditur_list"))


# --------------------------------------------------------------------------
# Pengaturan
# --------------------------------------------------------------------------
@app.route("/pengaturan", methods=["GET", "POST"])
def pengaturan():
    db = get_db()
    if request.method == "POST":
        fields = ["nama_perusahaan", "alamat", "kota", "judul_dokumen",
                  "subjudul", "nama_pud", "label_pud"]
        values = [request.form.get(f, "").strip() for f in fields]
        if not all(values):
            flash("Semua kolom pengaturan wajib diisi.", "error")
        else:
            db.execute(
                """UPDATE pengaturan SET
                   nama_perusahaan=?, alamat=?, kota=?, judul_dokumen=?,
                   subjudul=?, nama_pud=?, label_pud=? WHERE id=1""",
                values)
            db.commit()
            flash("Pengaturan disimpan.", "sukses")
        return redirect(url_for("pengaturan"))
    return render_template("pengaturan.html", p=get_pengaturan())


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
