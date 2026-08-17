from http.server import BaseHTTPRequestHandler
import requests
import json


COMCI_URL = "http://comci.net:4082/36179?NzM2MjlfNjQzNThfMF8x"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/134.0 Safari/537.36"
                ),
                "Referer": "http://comci.net/"
            }

            response = requests.get(
                COMCI_URL,
                headers=headers,
                timeout=15
            )

            result = {
                "success": True,
                "status": response.status_code,
                "content_type": response.headers.get("content-type"),
                "encoding": response.encoding,
                "text": response.text
            }

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps(
                    result,
                    ensure_ascii=False
                ).encode("utf-8")
            )

        except Exception as e:
            self.send_response(500)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps(
                    {
                        "success": False,
                        "error": str(e),
                        "type": type(e).__name__
                    },
                    ensure_ascii=False
                ).encode("utf-8")
            )
