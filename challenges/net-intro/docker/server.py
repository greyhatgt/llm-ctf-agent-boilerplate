import socketserver

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.sendall(b"Welcome! The flag is right here!\n")
        self.request.sendall(b"flag{n3tw0rk1ng_1s_c00l_right?}\n")

if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 9001
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        server.serve_forever()