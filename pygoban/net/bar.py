import sys
import time
import subprocess

process = subprocess.Popen(
    ["./foo.py"], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE
)


def run():

    while True:

        process.stdin.writelines(["a\r\n".encode()])
        process.stdin.flush()
        print("WAIT")
        inp = process.stdout.readline()
        print("got", inp.decode().strip())


if __name__ == "__main__":
    run()
