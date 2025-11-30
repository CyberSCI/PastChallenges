import base64
import logging
import socket
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

ADDRESS = "0.0.0.0"
PORT = 42000
MAX_PACKET = 32768
FLAGS = ["CyberSci{M0rse_th4n_ju5t_4_c0d3}", "CyberSci{R3qu3s7_gr4n73d}"]

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

# Overview
# 1. Receive request in morse code
# 2. Decode morse code, attempt to decode base32
# 3. Use HTTP request as normal
# 4. Reverse steps 1 and 2 for HTTP response

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
logger = logging.getLogger("telegraphic")

DEFAULT_HEADERS = {
    "Content-Type": "text/plain",
    "Connection": "close",
    "X-Flag-1": FLAGS[0],
}


@dataclass
class HttpRequest:
    method: bytes
    uri: bytes
    proto: bytes

    headers: dict[bytes, bytes]

    body: bytes


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


def normalize_line_endings(message: bytes) -> bytes:
    return message.replace(b"\r\n", b"\n")


def parse_http_request(http_message: bytes) -> HttpRequest:
    try:
        http_message = normalize_line_endings(http_message)
        request_head, request_body = http_message.split(b"\n\n", 1)
        headers_raw = request_head.splitlines()
        request_headline = headers_raw[0]
        request_headers = dict(
            header.split(b": ", 1) for header in headers_raw[1:]
        )
        request_method, request_uri, request_proto = request_headline.split(
            b" ", 3
        )

        parsed_message = HttpRequest(
            method=request_method,
            uri=request_uri,
            proto=request_proto,
            headers=request_headers,
            body=request_body,
        )
        return parsed_message
    except Exception as e:
        raise ValueError("Unable to parse request.") from e


def create_http_response(
    headers: dict[str, Any], body: bytes, status_code: HTTPStatus
) -> bytes:
    request_headers = DEFAULT_HEADERS.copy()
    request_headers.update(headers)
    response_headline = f"HTTP/1.0 {status_code} {status_code.phrase}"
    headers_raw = "\r\n".join(f"{k}: {v}" for k, v in request_headers.items())

    message = b"\r\n".join(
        [response_headline.encode(), headers_raw.encode() + b"\r\n", body]
    )

    return message


def recv_all(tcp_socket: socket.socket) -> bytes:
    prev_timeout = tcp_socket.gettimeout()
    rdata = []
    result = ""
    try:
        tcp_socket.settimeout(0.1)
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


def route_http_request(req: HttpRequest):
    # By default, we want to send a 404
    status_code = HTTPStatus.NOT_FOUND
    response_body = b"404: Not found."

    # TODO: Maybe add one more flag?
    # TODO: Maybe cracking a weak encryption scheme
    # I think using DES and some weak RSA should do it
    # Workflow
    # - User registers with the server
    # - User gets instructions to create an RSA key with e=1

    match req.uri:
        case b"/":
            # Give them flag 2
            # TODO: Sitemap here?
            response_body = FLAGS[1].encode()
            status_code = HTTPStatus.OK
        case _:
            # Default to 404
            pass

    response = create_http_response(
        {
            "Content-Length": len(response_body),
        },
        response_body,
        status_code,
    )
    logger.info("%s %s %s", req.method, req.uri, status_code)
    return response


def main():
    with socket.socket(
        socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP
    ) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_address = (ADDRESS, PORT)
        server_socket.bind(server_address)
        server_socket.listen(1)
        logger.info("Listening on %s:%s", ADDRESS, PORT)
        # This is to avoid the "'raw_request' is potentially unbound" error
        raw_request = None
        while True:
            client_socket, client_addr = server_socket.accept()
            with client_socket:
                try:
                    logger.debug("Connected to client IP: %s", client_addr)

                    raw_request = recv_all(client_socket)
                    logger.debug("Received: %s", raw_request)

                    decoded_request = decode_message(raw_request)
                    logger.debug("Decoded request: %s", decoded_request)

                    http_request = parse_http_request(decoded_request)
                    logger.debug("Parsed request: %s", http_request)

                    response = route_http_request(http_request)
                    logger.debug("Raw response:\n%s", response.decode())

                    encoded_response = encode_message(response)
                    logger.debug("Encoded response: %s", encoded_response)

                    client_socket.send(encoded_response)
                except ValueError as e:
                    logger.exception("%s request=%s", str(e), raw_request)

                    response_body = str(e).encode()
                    response = create_http_response(
                        {
                            "Content-Length": len(response_body),
                        },
                        response_body,
                        HTTPStatus.BAD_REQUEST,
                    )
                    logger.debug("Raw response:\n%s", response.decode())

                    encoded_response = encode_message(response)
                    logger.debug("Encoded response: %s", encoded_response)

                    client_socket.send(encoded_response)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutting down.")
