from socket import socket
from threading import Thread
from zlib import compress, decompress

from mss import mss
import pygame as pg

WIDTH = 1280
HEIGHT = 800


def retrieve_screenshot(conn: socket):
    with mss() as sct:
        rect = {"top": 0, "left": 0, "width": WIDTH, "height": HEIGHT}

        while True:
            img = sct.grab(rect)
            pixels = compress(img.rgb, 6)

            size = len(pixels)
            size_len = (size.bit_length() + 7) // 8
            conn.send(bytes([size_len]))

            size_bytes = size.to_bytes(size_len, "big")
            conn.send(size_bytes)

            conn.sendall(pixels)


def recvall(conn: socket, length: int) -> bytes:
    buffer = b""

    while len(buffer) < length:
        data = conn.recv(length - len(buffer))

        if not data:
            return data

        buffer += data

    return buffer


def main():
    mode = input("Tryb pracy (1: serwer, 2: client): ")

    if mode not in ("1", "2"):
        print("Niepoprawny tryb")
        main()
        return

    host = input("Host: ")
    port = int(input("Port: "))

    if mode == "1":
        sock = socket()
        sock.connect((host, port))

        try:
            sock.listen(5)
            print("Serwer włączony")

            while True:
                conn, addr = sock.accept()
                print(f"Podłączono z {addr[0]}:{addr[1]}")

                thread = Thread(target=retrieve_screenshot, args=(conn,))
                thread.start()
        finally:
            sock.close()
    elif mode == "2":
        pg.init()
        screen = pg.display.set_mode((WIDTH, HEIGHT))
        clock = pg.time.Clock()
        watching = True

        sock = socket()
        sock.connect((host, port))

        try:
            while watching:
                for event in pg.event.get():
                    if event.type == pg.QUIT:
                        watching = False
                        break

                size_len = int.from_bytes(sock.recv(1), byteorder="big")
                size = int.from_bytes(sock.recv(size_len), byteorder="big")
                pixels = decompress(recvall(sock, size))

                img = pg.image.fromstring(pixels, (WIDTH, HEIGHT), "RGB")

                screen.blit(img, (0, 0))
                pg.display.flip()
                clock.tick(60)
        finally:
            sock.close()


if __name__ == '__main__':
    main()
