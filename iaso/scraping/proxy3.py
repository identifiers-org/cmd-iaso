"""

Based off the proxy2.py Python 2.7 script by inaz2 (https://github.com/inaz2/proxy2)

Copyright (c) 2015, inaz2
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of proxy2 nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import ipaddress
import logging
import os
import select
import socket
import ssl
import threading
import time
import urllib.parse
from tempfile import NamedTemporaryFile, TemporaryDirectory

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from subprocess import Popen, PIPE

import click
import urllib3

urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:!aNULL:!eNULL"  #'ALL'


original_wrap_socket = ssl.SSLContext.wrap_socket


def new_wrap_socket(self, *args, **kwargs):
    if self.verify_mode == ssl.VerifyMode.CERT_NONE:
        # Allow all SSL and TLS versions (even unsecure ones)
        self.options = ssl.OP_ALL

    return original_wrap_socket(self, *args, **kwargs)


ssl.SSLContext.wrap_socket = new_wrap_socket


class ProxyRequestHandler(BaseHTTPRequestHandler):
    lock = threading.Lock()

    last_error = None

    def __init__(self, *args, **kwargs):
        self.tls = threading.local()
        self.tls.ssl = urllib3.PoolManager(
            maxsize=10, cert_reqs=ssl.VerifyMode.CERT_REQUIRED
        )  # ssl_version=ssl.PROTOCOL_TLSv1_2
        self.tls.rob = urllib3.PoolManager(
            maxsize=10, cert_reqs=ssl.VerifyMode.CERT_NONE
        )  # ssl_version=ssl.PROTOCOL_TLSv1_2

        self.logger = logging.getLogger("proxy3")

        if not self.logger.hasHandlers():
            self.logger.setLevel(logging.DEBUG)

            fh = logging.FileHandler("proxy3.log")
            fh.setLevel(logging.DEBUG)

            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            fh.setFormatter(formatter)

            self.logger.addHandler(fh)

        super().__init__(*args, **kwargs)

    def handle(self):
        try:
            super().handle()
        except Exception as err:
            self.log_error(repr(err))

    def log_error(self, format, *args):
        # surpress "Request timed out: timeout('timed out',)"
        if len(args) > 0 and isinstance(args[0], socket.timeout):
            return

        try:
            msg = str(format % args)
        except:
            msg = str(format) + " " + " - ".join(str(a) for a in args)

        if msg == "code 502, message Bad Gateway":
            return

        with self.lock:
            if msg == self.last_error:
                return

            self.last_error = msg

        self.logger.error(f"{self.command} {self.path} - {msg}")

    def log_message(self, format, *args):
        self.logger.debug(f"{self.command} {self.path} - {format % args}")

    def do_CONNECT(self):
        self.connect_intercept()

    def connect_intercept(self):
        hostname = self.path.split(":")[0]
        certpath = "%s/%s.crt" % (self.certdir.rstrip("/"), hostname)

        with self.lock:
            if not os.path.isfile(certpath):
                epoch = "%d" % (time.time() * 1000)

                p1 = Popen(
                    [
                        "openssl",
                        "req",
                        "-new",
                        "-key",
                        self.certkey,
                        "-subj",
                        "/CN=%s" % hostname,
                    ],
                    stdout=PIPE,
                )
                p2 = Popen(
                    [
                        "openssl",
                        "x509",
                        "-req",
                        "-days",
                        "3650",
                        "-CA",
                        self.cacert,
                        "-CAkey",
                        self.cakey,
                        "-set_serial",
                        epoch,
                        "-out",
                        certpath,
                    ],
                    stdin=p1.stdout,
                    stderr=PIPE,
                )

                p2.communicate()

        self.send_response(200, "Connection Established")
        self.end_headers()

        context = ssl.SSLContext(ssl.PROTOCOL_TLS)  # ssl.PROTOCOL_TLSv1_2
        context.load_cert_chain(certpath, keyfile=self.certkey)

        self.connection = context.wrap_socket(
            self.connection, server_side=True, do_handshake_on_connect=False
        )

        try:
            self.connection.do_handshake()
        except ssl.SSLError as err:
            self.log_error("line 185: %s", repr(err))
            if err.args[1].find("sslv3 alert") == -1:
                raise err

        self.rfile = self.connection.makefile("rb", self.rbufsize)
        self.wfile = self.connection.makefile("wb", self.wbufsize)

        conntype = self.headers.get("Proxy-Connection", "")
        if self.protocol_version == "HTTP/1.1" and conntype.lower() != "close":
            self.close_connection = 0
        else:
            self.close_connection = 1

    def do_GET(self):
        req = self
        content_length = int(req.headers.get("Content-Length", 0))
        req_body = self.rfile.read(content_length) if content_length else None

        if req.path[0] == "/":
            if isinstance(self.connection, ssl.SSLSocket):
                req.path = "https://%s%s" % (req.headers["Host"], req.path)
            else:
                req.path = "http://%s%s" % (req.headers["Host"], req.path)

        u = urllib.parse.urlsplit(req.path)
        scheme, netloc, path = (
            u.scheme,
            u.netloc,
            (u.path + "?" + u.query if u.query else u.path),
        )

        assert scheme in ("http", "https")

        if netloc:
            if "Host" in req.headers:
                req.headers.replace_header("Host", netloc)
            else:
                req.headers.add_header("Host", netloc)

        setattr(req, "headers", self.filter_headers(req.headers))

        try:
            try:
                request_time = time.perf_counter()

                res = self.tls.ssl.request(
                    req.command,
                    req.path,
                    body=req_body,
                    headers=dict(req.headers),
                    timeout=urllib3.util.Timeout(connect=req.timeout, read=req.timeout),
                    redirect=False,
                    retries=False,
                    preload_content=False,
                    enforce_content_length=False,
                    decode_content=False,
                )
            except (
                urllib3.exceptions.SSLError,
                urllib3.exceptions.MaxRetryError,
            ) as err:
                if isinstance(err, urllib3.exceptions.MaxRetryError) and not isinstance(
                    err.reason, urllib3.exceptions.SSLError
                ):
                    raise err

                request_time = time.perf_counter()

                res = self.tls.rob.request(
                    req.command,
                    req.path,
                    body=req_body,
                    headers=dict(req.headers),
                    timeout=urllib3.util.Timeout(connect=req.timeout, read=req.timeout),
                    redirect=False,
                    retries=False,
                    preload_content=False,
                    enforce_content_length=False,
                    decode_content=False,
                )

                self.send_header("X-SSL-Error", True)

            self.send_header("X-Response-Time", time.perf_counter() - request_time)

            try:
                socket = res._connection.sock or res._original_response.fp.raw._sock

                ip_address, port = socket.getpeername()
                ip_address = ipaddress.ip_address(ip_address)

                ip_address = (
                    f"[{ip_address}]" if ip_address.version == 6 else ip_address
                )

                self.send_header("X-IP-Port", f"{ip_address}:{port}")
            except Exception as err:
                self.log_error(1, repr(err))

            res.release_conn()

            version_table = {10: "HTTP/1.0", 11: "HTTP/1.1"}
            setattr(res, "response_version", version_table[res.version])

            res_body = []

            try:
                while True:
                    chunk = res.read(32, decode_content=False)

                    if not chunk:
                        break

                    res_body.append(chunk)
            except urllib3.exceptions.ProtocolError as err:
                self.send_header("X-Invalid-Response", True)

            res_body = b"".join(res_body)
        except urllib3.exceptions.ConnectTimeoutError:
            # Egregious DNS error such that we could not even connect to the resource
            self.wfile.write(
                f"{self.protocol_version} 204 DNS Error\r\n".encode("ascii")
            )

            self.send_header("Date", self.date_time_string())
            self.send_header("X-DNS-Error", True)
            self.send_header("Connection", "close")

            return self.end_headers()
        except urllib3.exceptions.ReadTimeoutError:
            return self.send_error(408)
        except urllib3.exceptions.SSLError:
            # Egregious SSL error such that we could not even perform the request in insecure mode
            self.wfile.write(
                f"{self.protocol_version} 204 SSL Error\r\n".encode("ascii")
            )

            self.send_header("Date", self.date_time_string())
            self.send_header("X-SSL-Error", True)
            self.send_header("Connection", "close")

            return self.end_headers()
        except urllib3.exceptions.ProtocolError:
            # Egregious protocol error such that we could not even perform the request
            self.wfile.write(
                f"{self.protocol_version} 204 Protocol Error\r\n".encode("ascii")
            )

            self.send_header("Date", self.date_time_string())
            self.send_header("X-Invalid-Response", True)
            self.send_header("Connection", "close")

            return self.end_headers()
        except Exception as err:
            self.log_error(repr(err))

            # Egregious *other* error such that we could not even perform the request
            self.wfile.write(f"{self.protocol_version} 204 {err}\r\n".encode("ascii"))

            self.send_header("Date", self.date_time_string())
            self.send_header("X-Invalid-Response", True)
            self.send_header("Connection", "close")

            return self.end_headers()

        res.headers["Content-Length"] = str(len(res_body))

        setattr(res, "headers", self.filter_headers(res.headers))

        self.wfile.write(
            ("%s %d %s\r\n" % (self.protocol_version, res.status, res.reason)).encode(
                "ascii"
            )
        )

        for key, value in res.headers.items():
            self.send_header(key, value)
        self.end_headers()

        if len(res_body) > 0:
            self.wfile.write(res_body)

        self.wfile.flush()

    do_HEAD = do_GET
    do_POST = do_GET
    do_PUT = do_GET
    do_DELETE = do_GET
    do_OPTIONS = do_GET

    def filter_headers(self, headers):
        # http://tools.ietf.org/html/rfc2616#section-13.5.1
        hop_by_hop = (
            "connection",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "transfer-encoding",
            "upgrade",
        )

        for k in hop_by_hop:
            if k in headers:
                del headers[k]

        # accept only supported encodings
        if "Accept-Encoding" in headers:
            ae = headers["Accept-Encoding"]
            filtered_encodings = [
                x.strip()
                for x in ae.split(",")
                if x.strip() in ("identity", "gzip", "x-gzip", "deflate")
            ]

            if isinstance(headers, urllib3.connection.HTTPHeaderDict):
                headers["Accept-Encoding"] = ", ".join(filtered_encodings)
            else:
                headers.replace_header("Accept-Encoding", ", ".join(filtered_encodings))

        return headers


def serve(
    port, timeout, ServerClass=ThreadingHTTPServer, protocol="HTTP/1.1",
):
    with NamedTemporaryFile() as cakey, NamedTemporaryFile() as cacert, NamedTemporaryFile() as certkey, TemporaryDirectory() as certdir:
        devnull = open(os.devnull, "w")

        Popen(
            ["openssl", "genrsa", "-out", cakey.name, "2048"],
            stdout=devnull,
            stderr=devnull,
        ).wait()
        Popen(
            [
                "openssl",
                "req",
                "-new",
                "-x509",
                "-days",
                "3650",
                "-key",
                cakey.name,
                "-out",
                cacert.name,
                "-subj",
                "/CN=proxy3 CA",
            ],
            stdout=devnull,
            stderr=devnull,
        ).wait()
        Popen(
            ["openssl", "genrsa", "-out", certkey.name, "2048"],
            stdout=devnull,
            stderr=devnull,
        ).wait()

        setattr(ProxyRequestHandler, "cakey", cakey.name)
        setattr(ProxyRequestHandler, "cacert", cacert.name)
        setattr(ProxyRequestHandler, "certkey", certkey.name)
        setattr(ProxyRequestHandler, "certdir", certdir)

        setattr(ProxyRequestHandler, "timeout", timeout)

        server_address = ("", port)

        ProxyRequestHandler.protocol_version = protocol
        httpd = ServerClass(server_address, ProxyRequestHandler)

        sa = httpd.socket.getsockname()

        click.echo(f"Serving HTTPS Proxy on {sa[0]}:{sa[1]} ...")

        httpd.serve_forever()

        click.echo(f"HTTPS Proxy on {sa[0]}:{sa[1]} was shut down.")
