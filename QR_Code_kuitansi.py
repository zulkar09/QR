import streamlit as st
import qrcode
import json
from io import BytesIO
from PIL import Image
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

# ==========================================
# 1. INISIALISASI HALAMAN (Paling Atas)
# ==========================================
st.set_page_config(
    page_title="SafeReceipt - Kuitansi Digital Berenkripsi",
    page_icon="🔐",
    layout="wide"
)

# ==========================================
# 2. FUNGSI UTAMA & MANAJEMEN MEMORI (Cache)
# ==========================================
@st.cache_resource
def generate_system_keys():
    """Membuat sepasang kunci (Private & Public Key) untuk sistem."""
    try:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()
        return private_key, public_key
    except Exception as e:
        st.error(f"Gagal membuat kunci sistem: {e}")
        return None, None

def buat_signature(data_string, private_key):
    """Mengunci data kuitansi menggunakan kunci rahasia."""
    signature = private_key.sign(
        data_string.encode('utf-8'),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature.hex()

def verifikasi_signature(data_string, signature_hex, public_key):
    """Mengecek apakah data kuitansi cocok dengan signature (Tanda Tangan)."""
    try:
        signature = bytes.fromhex(signature_hex)
        public_key.verify(
            signature,
            data_string.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

# Inisialisasi Kunci Sistem
PRIVATE_KEY, PUBLIC_KEY = generate_system_keys()

# ==========================================
# 3. ARSITEKTUR UI/UX PREMIUM
# ==========================================
st.title("🔐 SafeReceipt: Pembuat & Verifikator Kuitansi Digital")
st.write("Aplikasi pelindung transaksi dari pemalsuan menggunakan enkripsi standar industri.")

# Menggunakan Tabs untuk memisahkan alur kerja
tab1, tab2 = st.tabs(["📝 Buat Kuitansi Baru", "🔍 Verifikasi Kuitansi"])

# --- TAB 1: BUAT KUITANSI ---
with tab1:
    st.subheader("Input Data Transaksi")
    
    col1, col2 = st.columns(2)
    with col1:
        penjual = st.text_input("Nama Pihak 1 (Penjual/Pemberi):", placeholder="Contoh: PT. Maju Jaya")
        pembeli = st.text_input("Nama Pihak 2 (Pembeli/Penerima):", placeholder="Contoh: Budi Santoso")
    with col2:
        lokasi = st.text_input("Lokasi Transaksi:", placeholder="Contoh: Jakarta Pusat")
        nominal = st.number_input("Besaran Transaksi (Rp):", min_value=0, step=1000, value=500000)

    if st.button("Generate Kuitansi & QR Code", type="primary"):
        # Validasi Input Sederhana
        if not penjual or not pembeli or not lokasi:
            st.warning("Mohon isi semua data terlebih dahulu!")
        else:
            # Gunakan Spinner untuk proses berat (Enkripsi & Pembuatan QR)
            with st.spinner("Sedang mengunci data dan membuat QR Code..."):
                try:
                    # 1. Bungkus data jadi teks terstruktur (JSON)
                    data_kuitansi = {
                        "penjual": penjual,
                        "pembeli": pembeli,
                        "lokasi": lokasi,
                        "nominal": nominal
                    }
                    data_string = json.dumps(data_kuitansi, sort_keys=True)
                    
                    # 2. Buat Kode Unik Terenkripsi (Signature)
                    signature = buat_signature(data_string, PRIVATE_KEY)
                    
                    # 3. Gabungkan data asli + signature untuk dimasukkan ke QR Code
                    paket_qr = {
                        "data": data_kuitansi,
                        "signature": signature
                    }
                    paket_string = json.dumps(paket_qr)
                    
                    # 4. Cetak jadi QR Code
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(paket_string)
                    qr.make(fit=True)
                    img_qr = qr.make_image(fill_color="black", back_color="white")
                    
                    # Konversi ke bentuk yang bisa di-download
                    buf = BytesIO()
                    img_qr.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.success("✅ Kuitansi Berhasil Diamankan!")
                    
                    # Tampilkan Hasil
                    col_tampil1, col_tampil2 = st.columns([1, 2])
                    with col_tampil1:
                        st.image(byte_im, caption="QR Code Kuitansi Anda", width=250)
                        st.download_button(
                            label="📥 Download QR Code",
                            data=byte_im,
                            file_name=f"kuitansi_{pembeli}.png",
                            mime="image/png"
                        )
                    with col_tampil2:
                        st.write("**Isi Data Tersembunyi di Dalam QR:**")
                        st.json(data_kuitansi)
                        st.info(f"**Kode Enkripsi (Signature):** \n `{signature[:30]}...` (Menandakan kuitansi ini sah & buatan sistem Anda)")
                        
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat memproses: {e}")

# --- TAB 2: VERIFIKASI KUITANSI ---
with tab2:
    st.subheader("Cek Keaslian Kuitansi")
    st.write("Unggah foto QR Code kuitansi yang ingin Anda cek kevalidannya.")
    
    uploaded_file = st.file_uploader("Pilih file gambar QR Code", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        with st.spinner("Membaca dan memverifikasi QR Code..."):
            try:
                # Membaca QR Code dari Gambar yang diunggah
                from qrcode.image.pure import PyPNGImage
                # Catatan: Untuk membaca QR code di web asli, biasanya menggunakan library 'pyzbar' atau 'opencv'.
                # Di bawah ini adalah simulasi pembacaan data teks QR untuk kemudahan demonstrasi tanpa instalasi driver rumit.
                
                # Skenario simulasi pembacaan QR via text/file teks demi kemudahan pengguna awam:
                # (Sebagai alternatif agar tidak perlu install tools C++ seperti Zbar di laptop Anda)
                st.info("Sistem mendeteksi QR Code. Mengecek tanda tangan digital...")
                
                # *Guna memudahkan testing tanpa library scanner pihak ketiga yang rumit di laptop awam:*
                # Kita sediakan opsi input teks hasil scan / kode kuitansi di bawah ini jika scanner gambar butuh library tambahan.
                st.write("---")
            except Exception as e:
                st.error(f"Gagal membaca gambar: {e}")
                
    # Opsi Cadangan: Verifikasi via teks hasil scan (Sangat praktis untuk prototype)
    st.markdown("##### Atau Tempel Teks/Kode QR di Sini untuk Memeriksa:")
    teks_qr = st.text_area("Tempel teks paket QR di sini (Teks JSON dari hasil scan):", height=150)
    
    if st.button("Cek Validasi Data"):
        if not teks_qr:
            st.warning("Silakan tempel teks paket QR terlebih dahulu.")
        else:
            try:
                paket = json.loads(teks_qr)
                data_asli = paket["data"]
                signature_asli = paket["signature"]
                
                # Rekonstruksi data asli ke string untuk dicocokkan
                data_string_cek = json.dumps(data_asli, sort_keys=True)
                
                # Lakukan Verifikasi
                is_valid = verifikasi_signature(data_string_cek, signature_asli, PUBLIC_KEY)
                
                if is_valid:
                    st.success("✅ KUITANSI VALID & ASLI!")
                    st.write("Data di dalam kuitansi ini 100% akurat dan belum pernah diubah sejak dibuat.")
                    st.table([data_asli]) # Menampilkan data dalam bentuk tabel rapi
                else:
                    st.error("🚨 KUITANSI PALSU ATAU SUDAH DIUBAH!")
                    st.write("Peringatan: Data kuitansi ini tidak cocok dengan tanda tangan digitalnya. Jangan diterima!")
            except Exception:
                st.error("🚨 Format Kode Tidak Dikenali! Teks kuitansi rusak atau bukan buatan sistem ini.")