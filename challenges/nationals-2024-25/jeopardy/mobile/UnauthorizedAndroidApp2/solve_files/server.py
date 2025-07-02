import http.server, ssl

class LoggingHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        print(f"\n--- Received POST to {self.path} ---")
        print(self.headers)

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else b''

        print("Body:")
        print(body.decode(errors='replace')) 


        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        # Optional: quiet down default logging
        return

httpd = http.server.HTTPServer(('0.0.0.0', 443), LoggingHandler)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile='archives.valverde.vote.pem', keyfile='archives.valverde.vote-key.pem')

httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

print("Serving HTTPS on port 443")
httpd.serve_forever()