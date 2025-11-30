import copy
from io import BytesIO
from pathlib import Path

import pituophis as p
import pycurl
import structlog

logger = structlog.stdlib.get_logger("server")

PROTOCOL_BLACKLIST = ["file", "ftp"]


def search(request: p.Request):
    logger.debug("Requested URL.", requested_url=request.query)
    try:
        for protocol in PROTOCOL_BLACKLIST:
            if request.query.startswith(protocol):
                raise ValueError(f"Unauthorized protocol '{protocol}'")
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, request.query)
        c.setopt(pycurl.WRITEDATA, buffer)
        c.setopt(pycurl.SSL_VERIFYHOST, False)
        c.perform()
        c.close()

        response = buffer.getvalue().decode("iso-8859-1")
        return response

    except Exception as e:
        logger.exception("Error processing URL.")
        e = p.Item(
            itype="3",
            text=f"Error occurred trying to access {request.query}: {e}",
        )
        return e


def library(request: p.Request):
    library_dir = Path("library")

    menu = [
        p.Item(
            itype="1",
            text="Back to root",
            path="/",
            host=request.host,
            port=request.port,
        )
    ]
    try:
        path = (
            library_dir.joinpath(request.path.lstrip("/"))
            .resolve()
            .relative_to(library_dir.resolve())
        )

        logger.debug("Path requested", path=path)
        if not path.exists() or "flag" in path.as_posix().lower():
            raise FileNotFoundError
        if path.is_file():
            return path.read_bytes()

        if not path.is_dir():
            raise ValueError

        for sub_path in path.iterdir():
            itype = "i"
            if sub_path.is_file():
                itype = "0"
            elif sub_path.is_dir():
                itype = "1"
            menu.append(
                p.Item(
                    itype=itype, text=sub_path.name, path=sub_path.as_posix()
                )
            )

    except (ValueError, FileNotFoundError):
        logger.exception("Error searching for file.")
        return p.Item(itype="3", text=f"Unable to access {request.path}.")

    return menu


def alt_handler(request: p.Request):
    structlog.contextvars.bind_contextvars(client_ip=request.client)
    if request.path.startswith("/search"):
        return search(request)

    if request.path.startswith("/library"):
        return library(request)

    if request.path == "" or request.path == ".":
        with open("pub/gophermap") as fd:
            return p.parse_gophermap(fd.read(), def_port="13370")

    e = copy.copy(p.errors["404"])
    e.text = e.text.format(request.path)
    return e


def main():
    p.serve(port=13370, pub_dir="pub/", handler=alt_handler, debug=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Gopher server shutting down.")
