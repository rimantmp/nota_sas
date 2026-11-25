-- Skema basis data sistem nota (SQLite)

CREATE TABLE IF NOT EXISTS pengaturan (
    id              INTEGER PRIMARY KEY CHECK (id = 1),
    nama_perusahaan TEXT NOT NULL,
    alamat          TEXT NOT NULL,
    kota            TEXT NOT NULL,
    judul_dokumen   TEXT NOT NULL,
    subjudul        TEXT NOT NULL,
    nama_pud        TEXT NOT NULL,
    label_pud       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pupuk (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nama           TEXT NOT NULL,
    harga_per_ton  INTEGER NOT NULL,
    subjudul       TEXT NOT NULL DEFAULT '',
    aktif          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ppts (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    nama              TEXT NOT NULL,
    penanggung_jawab  TEXT NOT NULL,
    aktif             INTEGER NOT NULL DEFAULT 1
);

-- Satu PPTS dapat melayani banyak kecamatan.
CREATE TABLE IF NOT EXISTS ppts_kecamatan (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ppts_id   INTEGER NOT NULL REFERENCES ppts(id) ON DELETE CASCADE,
    nama      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_kec_ppts ON ppts_kecamatan (ppts_id);

CREATE TABLE IF NOT EXISTS ekspeditur (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nama     TEXT NOT NULL,
    no_pol   TEXT NOT NULL,
    aktif    INTEGER NOT NULL DEFAULT 1
);

-- Nota menyimpan snapshot nilai saat dibuat, agar nota lama tidak berubah
-- ketika data master (harga, nama, dsb.) diperbarui.
CREATE TABLE IF NOT EXISTS nota (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal_iso       TEXT NOT NULL,     -- YYYY-MM-DD (untuk urutan & filter)
    tanggal_tampil    TEXT NOT NULL,     -- "02 Juni 2026" (untuk cetak)
    nomor_so          TEXT NOT NULL,
    kuantum           REAL NOT NULL,

    pupuk_nama        TEXT NOT NULL,
    harga_per_ton     INTEGER NOT NULL,
    jumlah            INTEGER NOT NULL,

    ppts_nama         TEXT NOT NULL,
    kecamatan         TEXT NOT NULL,
    ppts_penandatangan TEXT NOT NULL,

    ekspeditur_nama   TEXT NOT NULL,
    no_pol            TEXT NOT NULL,

    nama_perusahaan   TEXT NOT NULL,
    alamat            TEXT NOT NULL,
    kota              TEXT NOT NULL,
    judul_dokumen     TEXT NOT NULL,
    subjudul          TEXT NOT NULL,
    nama_pud          TEXT NOT NULL,
    label_pud         TEXT NOT NULL,

    dibuat_at         TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_nota_tanggal ON nota (tanggal_iso);
CREATE INDEX IF NOT EXISTS idx_nota_so ON nota (nomor_so);
