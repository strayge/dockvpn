import SimpleHTTPServer
import SocketServer
import subprocess
from subprocess import PIPE, STDOUT
import urlparse
import os
import base64
import ssl
import time


if 'PORT_CONTROL' in os.environ.keys() and int(os.environ['PORT_CONTROL']):
    PORT = int(os.environ['PORT_CONTROL'])
else:
    PORT = 8000

SSL = True
if 'PORT_CONTROL' in os.environ.keys() and str(os.environ['PORT_CONTROL']).strip().lower() in ['0', 'false']:
    SSL = False

ALLOWED_CHARS = '0123456789abcdefghijklmnopqrstuvwxyz_'
CLIENTS_PATH = "/etc/openvpn/clients"
SSL_CRT_FILENAME = "/etc/openvpn/server.crt"
SSL_KEY_FILENAME = "/etc/openvpn/server.key"

USERNAME = os.environ['CONTROL_USERNAME'] if 'CONTROL_USERNAME' in os.environ.keys() else None
PASSWORD = os.environ['CONTROL_PASSWORD'] if 'CONTROL_PASSWORD' in os.environ.keys() else None
if not USERNAME or not PASSWORD:
    #print('Credentials for web service not provided. Web interface will not be enabled!')
    # prevent restart service
    time.sleep(3600)
    exit()

hashed_key = base64.b64encode(USERNAME + ":" + PASSWORD)

header = """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>VPN</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    </head>
    <body>
    <div class="container">
    <div class="page-header">
"""

footer = """
    </div>
    </div>
    </body>
    </html>
"""

def main_page():
    out = header
    out += "<h3>List of clients </h3>"
    if os.path.isdir(CLIENTS_PATH):
        out += """
        <table class="table table-striped">
        <thead><tr><th>Name</th><th>UDP</th><th>TCP</th></tr></thead><tbody>
        """
        for filename in os.listdir(CLIENTS_PATH):
            if filename.endswith('_tcp.ovpn'):
                client = filename[:-9]
                s= """
                <tr>
                <td>$client</td>
                <td> <a href='index.php?client=$client&type=udp'>$client_udp.ovpn</a> </td>
                <td> <a href='index.php?client=$client&type=tcp'>$client_tcp.ovpn</a> </td>
                </tr>
                """
                s = s.replace("$client", client)
                out += s
        out += "</tbody></table>"
    else:
        out += "<pre>clients directory not exists</pre>"
    out += """
    <h3>Actions</h3>
    <form action="index.php" method="get">Name: <input type="text" name="generate"><input type="submit" value="Create client"></form><br />
    <form action="index.php" method="get">Name: <input type="text" name="revoke"><input type="submit" value="Remove client"></form><br />
    """
    out += status_page();
    out += footer
    return out

def status_page():
    def readlog(filename):
        if not os.path.isfile(filename):
            return "<pre>%s not exists</pre>" % filename
        content = open(filename, 'rt').read().splitlines()
        out = """
        <table class="table table-striped">
        <thead><tr>
        <th>Client</th>
        <th>Int. Addr.</th>
        <th>DL (kB)</th>
        <th>UL (kB)</th>
        <th>Connected</th>
        </tr></thead><tbody>
        """
        for line in content:
                parts = line.split('      ')
                if parts[0] != 'CLIENT_LIST':
                    continue
                name = parts[1]
                ext_addr = parts[2]
                int_addr = parts[3]
                downloaded_kb = int(parts[4]) // 1024
                uploaded_kb = int(parts[5]) // 1024
                connected = parts[6]
                out += '<tr>'
                out += '<td>' + name + '</td>'
                #out += '<td>' + ext_addr + '</td>'
                out += '<td>' + int_addr + '</td>'
                out += '<td>' + downloaded_kb + '</td>'
                out += '<td>' + uploaded_kb + '</td>'
                out += '<td>' + connected + '</td>'
                out += '</tr>';
        out += '</tbody></table>'
        return out
    out = "<h3>Status</h3><h4>UDP</h4>"
    out += readlog('/etc/openvpn/logs/udp-status.log');
    out += "<h4>TCP</h4>"
    out += readlog('/etc/openvpn/logs/tcp-status.log');
    return out

def check_name(name):
    for c in name:
        if c not in ALLOWED_CHARS:
            return False
    return True

class Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def version_string(self):
        return "nginx"

    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf8")
        self.end_headers()

    def do_HEAD(self):
        try:
            self.send_error(200)
        except:
            pass

    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"whoami\"')
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def check_auth(self):
        if self.headers.getheader('Authorization') == 'Basic '+ hashed_key:
            return True
        else:
            self.do_AUTHHEAD()
            return False

    def do_GET(self):
        if not self.check_auth():
            return
        try:
            parts = urlparse.urlsplit(self.path)
            params = urlparse.parse_qs(parts.query)
            # add new client
            if 'generate' in params and params['generate'][0]:
                self._set_headers()
                self.wfile.write("<br /><a href='/'>Main page</a><br/><br/>")
                name = params['generate'][0]
                if not check_name(name):
                    self.wfile.write('not allowed character in name (allowed: %s)' % ALLOWED_CHARS)
                    return
                try:
                    out = subprocess.check_output(["generate_client", name])
                    self.wfile.write("<pre>" + out + "</pre>")
                except:
                    self.wfile.write("Error =(")
            # remove client
            elif 'revoke' in params and params['revoke'][0]:
                self._set_headers()
                self.wfile.write("<br /><a href='/'>Main page</a><br/><br/>")
                name = params['revoke'][0]
                if not check_name(name):
                    self.wfile.write('not allowed character in name (allowed: %s)' % ALLOWED_CHARS)
                    return
                try:
                    out = subprocess.check_output(["revoke_client", name])
                    self.wfile.write("<pre>" + out + "</pre>")
                except:
                    self.wfile.write("Error =(")
            # download ovpn config
            elif 'client' in params and params['client'][0]:
                name = params['client'][0]
                if not check_name(name):
                    self._set_headers()
                    self.wfile.write("<br /><a href='/'>Main page</a><br/><br/>")
                    self.wfile.write('not allowed character in name (allowed: %s)' % ALLOWED_CHARS)
                    return
                if 'type' not in params or params['type'][0] not in ['tcp','udp']:
                    self._set_headers()
                    self.wfile.write("<br /><a href='/'>Main page</a><br/><br/>")
                    self.wfile.write('wrong type specified')
                    return
                proto = params['type'][0]
                filename = "%s_%s.ovpn" %  (name, proto)
                fullpath = "%s/%s" %  (CLIENTS_PATH, filename)
                if not os.path.isfile(fullpath):
                    self._set_headers()
                    self.wfile.write("<br /><a href='/'>Main page</a><br/><br/>")
                    self.wfile.write('client not exists')
                    return
                ovpn = open(fullpath, 'rt').read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Disposition', 'attachment; filename="%s"' % filename)
                self.end_headers()
                self.wfile.write(ovpn)
            else:
                self._set_headers()
                self.wfile.write(main_page())
        except:
            self.send_error(200)

httpd = SocketServer.TCPServer(("", PORT), Handler)
if SSL:
    httpd.socket = ssl.wrap_socket (httpd.socket, certfile=SSL_CRT_FILENAME, keyfile=SSL_KEY_FILENAME, server_side=True)
    print('starting web_control daemon with ssl...')
else:
    print('starting web_control daemon without ssl...')

httpd.serve_forever()
