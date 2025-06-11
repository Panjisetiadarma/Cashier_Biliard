import datetime
from collections import deque
import time
import threading

class MejaBilliard:
    def __init__(self, nomor):
        self.nomor = nomor
        self.status = "kosong"  # kosong, terisi, menunggu pembayaran
        self.pelanggan = None
        self.waktu_mulai = None
        self.waktu_habis = None  # Waktu sebenarnya ketika sewa habis
        self.estimasi_selesai = None
        self.durasi_sewa = 0
        self.pesanan = []
        self.lampu = False

class Pelanggan:
    def __init__(self, nama):
        self.nama = nama
        self.meja = None
        self.total_biaya = 0

class MenuItem:
    def __init__(self, nama, harga, jenis):
        self.nama = nama
        self.harga = harga
        self.jenis = jenis  # makanan/minuman

class SistemKasirBilliard:
    def __init__(self):
        self.meja = [MejaBilliard(i+1) for i in range(10)]  # 10 meja
        self.antrian = deque()
        self.riwayat_transaksi = []
        self.menu = [
            MenuItem("Kentang Goreng", 15000, "makanan"),
            MenuItem("Nasi Goreng", 25000, "makanan"),
            MenuItem("Ayam Goreng", 30000, "makanan"),
            MenuItem("Es Teh", 8000, "minuman"),
            MenuItem("Es Jeruk", 10000, "minuman"),
            MenuItem("Kopi", 12000, "minuman")
        ]
        self.harga_per_jam = 50000  # Harga sewa per jam
        self.monitor_active = True
        self.monitor_thread = threading.Thread(target=self.monitor_waktu_sewa)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def __del__(self):
        self.monitor_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)

    def monitor_waktu_sewa(self):
        """Thread terpisah untuk memantau waktu sewa secara real-time"""
        while self.monitor_active:
            sekarang = datetime.datetime.now()
            for meja in self.meja:
                if meja.status == "terisi" and meja.estimasi_selesai and meja.estimasi_selesai <= sekarang:
                    meja.lampu = False
                    meja.status = "menunggu pembayaran"
                    meja.waktu_habis = sekarang
                    print(f"\n[PENTING] Waktu sewa meja {meja.nomor} ({meja.pelanggan.nama}) telah habis!")
                    print("Lampu dimatikan. Silakan lakukan pembayaran.")
                    # Tampilkan peringatan di atas menu
                    print("\n" + "="*50)
            time.sleep(5)  # Periksa setiap 5 detik

    def cari_meja_kosong(self):
        return [m for m in self.meja if m.status == "kosong"]
    
    def cari_meja_menunggu_pembayaran(self):
        return [m for m in self.meja if m.status == "menunggu pembayaran"]

    def cari_pelanggan_aktif(self, identitas):
        try:
            nomor_meja = int(identitas)
            meja = next(m for m in self.meja if m.nomor == nomor_meja and m.status in ["terisi", "menunggu pembayaran"])
            return meja.pelanggan, meja
        except (ValueError, StopIteration):
            for m in self.meja:
                if m.status in ["terisi", "menunggu pembayaran"] and m.pelanggan.nama.lower() == identitas.lower():
                    return m.pelanggan, m
            return None, None

    def tampilkan_menu(self):
        print("\n=== MENU MAKANAN & MINUMAN ===")
        for i, item in enumerate(self.menu, 1):
            print(f"{i}. {item.nama} - Rp {item.harga:,.0f} ({item.jenis})")

    def input_pelanggan_baru(self):
        nama = input("Masukkan nama pelanggan: ")
        pelanggan = Pelanggan(nama)
        
        meja_kosong = self.cari_meja_kosong()
        if not meja_kosong:
            self.antrian.append(pelanggan)
            print("Semua meja penuh, Anda masuk antrian.")
            return
        
        print("Meja yang tersedia:", [m.nomor for m in meja_kosong])
        nomor_meja = int(input("Pilih nomor meja: "))
        meja = next(m for m in meja_kosong if m.nomor == nomor_meja)
        
        durasi = int(input("Masukkan durasi sewa (menit): "))
        
        self.aktifkan_meja(meja, pelanggan, durasi)
        self.tawarkan_menu(pelanggan)
    
    def aktifkan_meja(self, meja, pelanggan, durasi):
        meja.status = "terisi"
        meja.pelanggan = pelanggan
        meja.durasi_sewa = durasi
        meja.waktu_mulai = datetime.datetime.now()
        meja.estimasi_selesai = meja.waktu_mulai + datetime.timedelta(minutes=durasi)
        meja.lampu = True
        pelanggan.meja = meja
        pelanggan.total_biaya = (durasi / 60) * self.harga_per_jam
        
        print(f"Meja {meja.nomor} aktif untuk {pelanggan.nama} selama {durasi} menit.")
    
    def tawarkan_menu(self, pelanggan):
        jawaban = input("Apakah ingin memesan makanan/minuman? (y/n): ").lower()
        if jawaban == 'y':
            self.tampilkan_menu()
            pilihan = int(input("Pilih nomor menu: "))
            qty = int(input("Jumlah: "))
            
            item = self.menu[pilihan-1]
            pelanggan.meja.pesanan.append({"item": item, "qty": qty})
            pelanggan.total_biaya += item.harga * qty
            
            print(f"{item.nama} x{qty} ditambahkan ke pesanan.")

    def tambahan_pesanan(self):
        identitas = input("Masukkan nama pelanggan atau nomor meja: ")
        pelanggan, meja = self.cari_pelanggan_aktif(identitas)
        
        if not pelanggan:
            print("Pelanggan tidak ditemukan atau sewa sudah selesai.")
            return
        
        self.tampilkan_menu()
        pilihan = int(input("Pilih nomor menu: "))
        qty = int(input("Jumlah: "))
        
        item = self.menu[pilihan-1]
        meja.pesanan.append({"item": item, "qty": qty})
        pelanggan.total_biaya += item.harga * qty
        
        print(f"{item.nama} x{qty} ditambahkan ke pesanan.")

    def pembayaran(self):
        identitas = input("Masukkan nama pelanggan atau nomor meja: ")
        pelanggan, meja = self.cari_pelanggan_aktif(identitas)
        
        if not pelanggan:
            print("Pelanggan tidak ditemukan atau sewa sudah selesai.")
            return
        
        # Hitung durasi aktual
        if meja.status == "terisi":
            durasi_aktual = (datetime.datetime.now() - meja.waktu_mulai).total_seconds() / 60
        else:  # status menunggu pembayaran
            durasi_aktual = (meja.waktu_habis - meja.waktu_mulai).total_seconds() / 60
        
        biaya_sewa = (durasi_aktual / 60) * self.harga_per_jam
        
        print("\n=== RINCIAN PEMBAYARAN ===")
        print(f"Pelanggan: {pelanggan.nama}")
        print(f"Meja: {meja.nomor}")
        print(f"Waktu mulai: {meja.waktu_mulai.strftime('%d/%m/%Y %H:%M')}")
        
        if meja.status == "terisi":
            print(f"Waktu selesai: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
        else:
            print(f"Waktu habis: {meja.waktu_habis.strftime('%d/%m/%Y %H:%M')}")
            
        print(f"Durasi: {durasi_aktual:.2f} menit")
        print(f"Biaya sewa: Rp {biaya_sewa:,.0f}")
        
        if meja.pesanan:
            print("\nPesanan:")
            for p in meja.pesanan:
                print(f"- {p['item'].nama} x{p['qty']}: Rp {p['item'].harga * p['qty']:,.0f}")
        
        total = biaya_sewa + sum(p['item'].harga * p['qty'] for p in meja.pesanan)
        print(f"\nTOTAL: Rp {total:,.0f}")
        
        konfirmasi = input("Konfirmasi pembayaran (y/n): ").lower()
        if konfirmasi == 'y':
            self.simpan_transaksi(pelanggan, meja, durasi_aktual, total)
            self.nonaktifkan_meja(meja)
            print("Pembayaran berhasil. Terima kasih!")
    
    def simpan_transaksi(self, pelanggan, meja, durasi, total):
        transaksi = {
            "tanggal": datetime.datetime.now(),
            "pelanggan": pelanggan.nama,
            "meja": meja.nomor,
            "waktu_mulai": meja.waktu_mulai,
            "waktu_selesai": meja.waktu_habis if meja.status == "menunggu pembayaran" else datetime.datetime.now(),
            "durasi": durasi,
            "pesanan": meja.pesanan.copy(),
            "total": total,
            "status": "selesai"
        }
        self.riwayat_transaksi.append(transaksi)
    
    def nonaktifkan_meja(self, meja):
        meja.status = "kosong"
        meja.pelanggan = None
        meja.waktu_mulai = None
        meja.waktu_habis = None
        meja.estimasi_selesai = None
        meja.durasi_sewa = 0
        meja.pesanan = []
        meja.lampu = False

    def cek_antrian(self):
        if not self.antrian:
            print("Antrian kosong.")
            return

        print("\n=== DAFTAR ANTRIAN ===")
        for i, pelanggan in enumerate(self.antrian, 1):
            print(f"{i}. {pelanggan.nama}")

        print("\nPilihan:")
        print("1. Hapus pelanggan dari antrian")
        print("2. Kembali")
        pilihan = input("Pilih (1-2): ")

        if pilihan == "1":
            nomor = int(input("Masukkan nomor urut pelanggan yang dihapus: "))
            if 1 <= nomor <= len(self.antrian):
                # Convert deque to list untuk akses indeks
                antrian_list = list(self.antrian)
                pelanggan = antrian_list[nomor-1]
                antrian_list.pop(nomor-1)
                self.antrian = deque(antrian_list)
                print(f"Pelanggan {pelanggan.nama} dihapus dari antrian.")
            else:
                print("Nomor tidak valid.")

    def tampilkan_riwayat(self):
        print("\n=== RIWAYAT TRANSAKSI ===")
        
        print("Filter berdasarkan:")
        print("1. Hari ini")
        print("2. Minggu ini")
        print("3. Bulan ini")
        print("4. Semua")
        print("5. Rentang tanggal kustom")
        pilihan = input("Pilih filter (1-5): ")
        
        transaksi_filter = self.riwayat_transaksi.copy()
        today = datetime.datetime.now().date()
        
        if pilihan == "1":
            transaksi_filter = [t for t in transaksi_filter if t['tanggal'].date() == today]
        elif pilihan == "2":
            start_date = today - datetime.timedelta(days=7)
            transaksi_filter = [t for t in transaksi_filter if t['tanggal'].date() >= start_date]
        elif pilihan == "3":
            start_date = today - datetime.timedelta(days=30)
            transaksi_filter = [t for t in transaksi_filter if t['tanggal'].date() >= start_date]
        elif pilihan == "5":
            start = input("Tanggal awal (dd/mm/yyyy): ")
            end = input("Tanggal akhir (dd/mm/yyyy): ")
            start_date = datetime.datetime.strptime(start, "%d/%m/%Y").date()
            end_date = datetime.datetime.strptime(end, "%d/%m/%Y").date()
            transaksi_filter = [t for t in transaksi_filter if start_date <= t['tanggal'].date() <= end_date]
        
        print("\nUrutkan berdasarkan:")
        print("1. Tanggal (terbaru)")
        print("2. Nama Pelanggan")
        print("3. Nomor Meja")
        sort_by = input("Pilih sorting (1-3): ")
        
        if sort_by == "1":
            transaksi_filter.sort(key=lambda x: x['tanggal'], reverse=True)
        elif sort_by == "2":
            transaksi_filter.sort(key=lambda x: x['pelanggan'])
        elif sort_by == "3":
            transaksi_filter.sort(key=lambda x: x['meja'])
        
        for t in transaksi_filter:
            print("\n=== TRANSAKSI ===")
            print(f"Tanggal: {t['tanggal'].strftime('%d/%m/%Y %H:%M')}")
            print(f"Pelanggan: {t['pelanggan']}")
            print(f"Meja: {t['meja']}")
            print(f"Waktu: {t['waktu_mulai'].strftime('%H:%M')} - {t['waktu_selesai'].strftime('%H:%M')}")
            print(f"Durasi: {t['durasi']:.2f} menit")
            
            if t['pesanan']:
                print("\nPesanan:")
                for p in t['pesanan']:
                    print(f"- {p['item'].nama} x{p['qty']}: Rp {p['item'].harga * p['qty']:,.0f}")
            
            print(f"\nTotal: Rp {t['total']:,.0f}")
            print(f"Status: {t['status']}")
            print("="*20)

def main():
    sistem = SistemKasirBilliard()
    
    while True:
        print("\n=== SISTEM KASIR BILLIARD ===")
        print("1. Input Pelanggan Baru")
        print("2. Tambahan Pesanan")
        print("3. Pembayaran")
        print("4. Cek Antrian")
        print("5. Riwayat Transaksi")
        print("6. Keluar")
        
        pilihan = input("Pilih menu (1-6): ")
        
        if pilihan == "1":
            sistem.input_pelanggan_baru()
        elif pilihan == "2":
            sistem.tambahan_pesanan()
        elif pilihan == "3":
            sistem.pembayaran()
        elif pilihan == "4":
            sistem.cek_antrian()
        elif pilihan == "5":
            sistem.tampilkan_riwayat()
        elif pilihan == "6":
            print("Terima kasih, program selesai.")
            break
        else:
            print("Pilihan tidak valid. Silakan coba lagi.")

if __name__ == "__main__":
    main()