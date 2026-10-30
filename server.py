import socket
import threading
import json
import time

HOST = "0.0.0.0"   # dengarkan di semua interface agar laptop lain bisa konek
PORT = 5000
MAKS_NAMA = 50

clients = {}                    # nama -> socket
kunci = threading.Lock()        # melindungi dict 'clients' dari akses bersamaan
kunci_kirim = threading.Lock()  # mencegah pesan dari beberapa thread saling tercampur


def jam():
    return time.strftime("%H:%M")


def kirim(sock, data):
    with kunci_kirim:
        sock.sendall((json.dumps(data) + "\n").encode("utf-8"))


def broadcast(data, kecuali=None):
    with kunci:
        daftar = list(clients.items())
    for nama, s in daftar:
        if nama != kecuali:
            try:
                kirim(s, data)
            except OSError:
                pass  # client sudah putus, akan dibersihkan thread-nya sendiri


def cari_user(nama_input):
    with kunci:
        for nama, s in clients.items():
            if nama.lower() == nama_input.lower():
                return nama, s
    return None, None


def validasi_nama(calon):
    if not calon:
        return "Nama tidak boleh kosong."
    if " " in calon:
        return "Nama tidak boleh mengandung spasi."
    if len(calon) > MAKS_NAMA:
        return f"Nama maksimal {MAKS_NAMA} karakter."
    if calon.upper() == "SERVER":
        return "Nama 'SERVER' dicadangkan."
    return None


def tahap_join(conn, f):
    while True:
        baris = f.readline()
        if not baris:
            return None  # client menutup koneksi
        try:
            pesan = json.loads(baris)
        except json.JSONDecodeError:
            kirim(conn, {"type": "error", "text": "Format pesan tidak valid."})
            continue
        if pesan.get("type") != "join":
            kirim(conn, {"type": "error", "text": "Kirim 'join' dengan nama terlebih dahulu."})
            continue

        calon = str(pesan.get("name", "")).strip()
        alasan = validasi_nama(calon)
        if alasan:
            kirim(conn, {"type": "error", "text": alasan})
            continue

        # Cek duplikat + daftarkan dalam SATU kunci agar tidak ada race condition
        with kunci:
            dipakai = any(n.lower() == calon.lower() for n in clients)
            if not dipakai:
                clients[calon] = conn
        if dipakai:
            kirim(conn, {"type": "error", "text": f"Nama '{calon}' sudah dipakai, coba nama lain."})
            continue

        kirim(conn, {"type": "join_ok"})
        return calon


def layani_client(conn, addr):
    f = conn.makefile("r", encoding="utf-8")  # baca per baris
    nama = None
    try:
        nama = tahap_join(conn, f)
        if nama is None:
            return

        print(f"[+] {nama} terhubung dari {addr[0]}:{addr[1]}")
        with kunci:
            online = len(clients)
        kirim(conn, {"type": "info",
                     "text": f"Selamat datang, {nama}! Ada {online} user online. Ketik /help untuk bantuan."})
        broadcast({"type": "info", "text": f"{nama} bergabung ke chat."}, kecuali=nama)

        # Loop utama: baca pesan client baris demi baris
        for baris in f:
            try:
                pesan = json.loads(baris)
            except json.JSONDecodeError:
                kirim(conn, {"type": "error", "text": "Format pesan tidak valid."})
                continue
            tipe = pesan.get("type")

            if tipe in ("all", "msg"):
                teks = str(pesan.get("text", "")).strip()
                if teks:
                    print(f"[{nama}] {teks}")
                    broadcast({"type": "chat", "from": nama, "text": teks, "time": jam()})

            elif tipe == "pm":
                teks = str(pesan.get("text", "")).strip()
                tujuan, sock_tujuan = cari_user(str(pesan.get("to", "")))
                if sock_tujuan is None:
                    kirim(conn, {"type": "error", "text": f"User '{pesan.get('to')}' tidak ditemukan."})
                elif tujuan == nama:
                    kirim(conn, {"type": "error", "text": "Tidak bisa mengirim PM ke diri sendiri."})
                elif teks:
                    kirim(sock_tujuan, {"type": "pm", "from": nama, "text": teks, "time": jam()})
                    kirim(conn, {"type": "pm_sent", "to": tujuan, "text": teks, "time": jam()})

            elif tipe == "users":
                with kunci:
                    daftar = ", ".join(clients.keys())
                    jumlah = len(clients)
                kirim(conn, {"type": "info", "text": f"Online ({jumlah}): {daftar}"})

            elif tipe == "quit":
                break

            else:
                kirim(conn, {"type": "error", "text": "Tipe pesan tidak dikenal."})

    except (ConnectionError, OSError):
        pass  # client putus mendadak
    finally:
        # Bersihkan client yang keluar
        if nama:
            with kunci:
                clients.pop(nama, None)
            print(f"[-] {nama} terputus")
            broadcast({"type": "info", "text": f"{nama} meninggalkan chat."})
        f.close()
        conn.close()


def chat_all_server():
    while True:
        try:
            teks = input().strip()
        except EOFError:
            return
        if not teks:
            continue
        if teks == "/users":
            with kunci:
                daftar = ", ".join(clients.keys()) or "(kosong)"
            print(f"Online: {daftar}")
        else:
            broadcast({"type": "chat", "from": "SERVER", "text": teks, "time": jam()})
            print(f"[SERVER -> semua] {teks}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server berjalan di port {PORT}")
    print("Ketik pesan lalu Enter untuk chat ke semua user. /users = lihat user online.")

    # Thread terpisah agar input konsol tidak memblokir accept()
    threading.Thread(target=chat_all_server, daemon=True).start()

    try:
        while True:
            conn, addr = server.accept()
            # Satu thread per client agar tidak saling memblokir
            threading.Thread(target=layani_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
