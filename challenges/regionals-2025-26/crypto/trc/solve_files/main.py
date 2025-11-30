import base64
import socket

ADDRESS = "127.0.0.1"  # Replace this with whatever the actual server address is
PORT = 42000
MAX_PACKET = 32768

MORSE_CODE_DICT = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    "0": "-----",
    ", ": "--..--",
    ".": ".-.-.-",
    "?": "..--..",
    "/": "-..-.",
    "-": "-....-",
    "(": "-.--.",
    ")": "-.--.-",
    "=": "-...-",
}
# Reverse lookup table
MORSE_CODE_REVERSE_DICT = {v: k for k, v in MORSE_CODE_DICT.items()}


def recv_all(tcp_socket: socket.socket) -> bytes:
    prev_timeout = tcp_socket.gettimeout()
    rdata = []
    result = ""
    try:
        tcp_socket.settimeout(1)
        while True:
            data = tcp_socket.recv(MAX_PACKET)
            if data == b"":
                break
            rdata.append(data)
    except TimeoutError:
        pass
    finally:
        tcp_socket.settimeout(prev_timeout)

    result = b"".join(rdata)

    return result


def encode_message(text: bytes) -> bytes:
    b32_encoded = base64.b32encode(text).decode()
    fully_encoded = ""
    for letter in b32_encoded:
        if letter == " ":
            fully_encoded += " "
            continue

        character = MORSE_CODE_DICT.get(letter)
        if character is None:
            raise ValueError(f"Unsupported Morse character: {letter}")

        fully_encoded += character + " "

    return fully_encoded.encode()


def decode_message(encoded: bytes) -> bytes:
    encoded += b" "
    b32_encoded = ""
    morse_char = ""

    spaces = 0

    for letter in encoded.decode():
        if letter == "\n":
            continue
        is_space = letter == " "
        if not is_space:
            spaces = 0
            morse_char += letter
            continue

        spaces += 1
        if spaces == 2:
            b32_encoded += " "
            continue

        character = MORSE_CODE_REVERSE_DICT.get(morse_char)
        if character is None:
            raise ValueError(f"Invalid Morse character: {morse_char}")
        b32_encoded += character
        morse_char = ""

    b32_encoded = b32_encoded.strip()
    text = base64.b32decode(b32_encoded.encode())
    return text


def part1():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((ADDRESS, PORT))
        client_socket.sendall(b"Hello, world!")
        response = recv_all(client_socket)
        decoded_response = decode_message(response)
        response_lines = decoded_response.splitlines()
        for line in response_lines:
            # Checking for our header
            if not line.startswith(b"X-Flag-1"):
                continue

            header_name, flag = line.split(b": ", 1)
            print(flag.decode())


def part2():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((ADDRESS, PORT))
        request = b"GET / HTTP/1.0\r\nAccept: */*\r\n\r\n"
        encoded_request = encode_message(request)
        client_socket.sendall(encoded_request)
        response = recv_all(client_socket)
        decoded_response = decode_message(response)
        response_lines = decoded_response.splitlines()
        for line in response_lines:
            if line.startswith(b"CyberSci"):
                print(line.decode())


def main():
    part1()
    part2()


if __name__ == "__main__":
    main()
