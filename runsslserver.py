import os
import ssl
from http.server import HTTPServer
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application

# Ensure this points to your settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eco_sys.settings')
application = get_wsgi_application()

def runsslserver():
    addr = 'localhost'
    port = 8000
    httpd = HTTPServer((addr, port), application)
    httpd.socket = ssl.wrap_socket(httpd.socket,
                                server_side=True,
                                keyfile="key.pem",
                                certfile="cert.pem",
                                ssl_version=ssl.PROTOCOL_TLS)
    print(f'Serving HTTPS on {addr} port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    execute_from_command_line(['manage.py', 'runsslserver'])
