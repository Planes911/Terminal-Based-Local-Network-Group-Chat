import socket
import threading
import json
import sys
import os

HELP = """\
Commands:
  <pesan>             kirim ke semua user (chat room)
  /all <pesan>        kirim ke semua user (sama seperti di atas)
  /pm <nama> <pesan>  kirim pesan privat
  /users              lihat user yang online
  /help               tampilkan bantuan ini
  /quit               keluar"""


def kirim(sock, data):
    sock.sendall((json.dumps(data) + "\n").encode("utf-8"))


def tampil(teks):
    print(f"\r{teks}")
    print("> ", end="", flush=True)


def terima(f, nama):
    try:
        for baris in f:
            pesan = json.loads(baris)
            tipe = pesan.get("type")
            waktu = pesan.get("time", "")
            if tipe == "chat":
                pengirim = "Kamu" if pesan["from"] == nama else pesan["from"]
                tampil(f"[{waktu}] {pengirim}: {pesan['text']}")
            elif tipe == "pm":
                tampil(f"[{waktu}] (PM dari {pesan['from']}) {pesan['text']}")
            elif tipe == "pm_sent":
                tampil(f"[{waktu}] (PM ke {pesan['to']}) {pesan['text']}")
            elif tipe == "info":
                tampil(f"* {pesan['text']}")
            elif tipe == "error":
                tampil(f"! {pesan['text']}")
    except (ConnectionError, OSError, json.JSONDecodeError):
        pass
    print("\nKoneksi ke server terputus.")
    os._exit(0)  # hentikan seluruh program (thread utama sedang menunggu input)


def minta_nama(sock, f):
    while True:
        nama = input("Masukkan nama (tanpa spasi): ").strip()
        if not nama:
            print("! Nama tidak boleh kosong.")
            continue
        kirim(sock, {"type": "join", "name": nama})
        baris = f.readline()  # menunggu jawaban server
        if not baris:
            print("Server menutup koneksi.")
            return None
        jawab = json.loads(baris)
        if jawab.get("type") == "join_ok":
            return nama
        print(f"! {jawab.get('text', 'Nama ditolak.')}")  # minta loop lagi


def main():
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        host = input("Alamat server [127.0.0.1]: ").strip() or "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
    try:
        sock.connect((host, port))
    except OSError as e:
        print(f"Gagal terhubung ke {host}:{port} -> {e}")
        return

    f = sock.makefile("r", encoding="utf-8")
    try:
        nama = minta_nama(sock, f)
        if nama is None:
            return

        # Thread terpisah agar menerima pesan tidak menghalangi pengetikan pesan/command
        threading.Thread(target=terima, args=(f, nama), daemon=True).start()

        while True:
            teks = input("> ").strip()
            if not teks:
                continue
            if teks == "/quit":
                kirim(sock, {"type": "quit"})
                break
            elif teks == "/help":
                print(HELP)
            elif teks == "/users":
                kirim(sock, {"type": "users"})
            elif teks.startswith("/pm"):
                bagian = teks.split(" ", 2)
                if len(bagian) < 3 or not bagian[2].strip():
                    print("Format: /pm <nama> <pesan>")
                else:
                    kirim(sock, {"type": "pm", "to": bagian[1], "text": bagian[2]})
            elif teks.startswith("/all"):
                isi = teks[4:].strip()
                if not isi:
                    print("Format: /all <pesan>")
                else:
                    kirim(sock, {"type": "all", "text": isi})
            elif teks.startswith("/"):
                print("Perintah tidak dikenal. Ketik /help.")
            else:
                kirim(sock, {"type": "all", "text": teks})  # teks biasa = chat ke semua
    except (KeyboardInterrupt, EOFError):
        try:
            kirim(sock, {"type": "quit"})
        except OSError:
            pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()
