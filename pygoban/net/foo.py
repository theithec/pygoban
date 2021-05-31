#!  /usr/bin/env python

import sys
import time
import socket

HOST = "localhost"  # The remote host
PORT = 50007  # The same port as used by the server


def run():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(">>>>>>S1", s)
        s.connect((HOST, PORT))
        print(">>>>>>S2", s)
        while True:
            inp = sys.stdin.readline().strip()
            print(">>>>>", inp)
            if inp == "quit":
                break

            if inp.startswith(f"genmove"):
                s.sendall(inp.encode())
                data = s.recv(1024)
                print(">>>>>>data", data)
                sys.stdout.writelines([data.decode()])
                sys.stdout.flush()

            sys.stdout.writelines(["\r\n"])
            sys.stdout.flush()
            time.sleep(0.1)


if __name__ == "__main__":
    run()
