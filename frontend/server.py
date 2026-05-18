import http.server
import socketserver
import os

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/index_complete.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

os.chdir('/home/pallavi/toll-vehicle-detection/frontend')
with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Frontend server running at http://localhost:{PORT}")
    print("Open your browser to access TollPlaza AI Dashboard")
    httpd.serve_forever()
