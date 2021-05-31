# Echo server program
import socket

HOST = ""  # Symbolic name meaning all available interfaces
PORT = 50007  # Arbitrary non-privileged port

a = 0
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    conn, addr = s.accept()
    with conn:
        print("Connected by", addr)
        while True:
            inp = conn.recv(1024).decode()
            print("INP", inp)
            if inp.startswith("genmove"):
                a += 1
                data = f"= A{a}\r\n"
            conn.sendall(data.encode())
