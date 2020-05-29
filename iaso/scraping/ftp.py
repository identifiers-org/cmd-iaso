import re
import time
import urllib

from contextlib import closing
from datetime import datetime, timezone

from .content_type import get_mime_type, get_encoding, get_content_type, decode_content

FTP_STATUS_PATTERN = re.compile(r"([1-6][0-9][0-9])")


async def scrape_ftp_resource(url, timeout):
    request_date = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)

    request_time = time.perf_counter()

    try:
        with closing(urllib.request.urlopen(url, timeout=timeout)) as r:
            content = r.read()

            response_time = time.perf_counter() - request_time

            redirects = [
                {
                    "url": url,
                    "ip_port": None,
                    "response_time": int(round(response_time, 3) * 1000),
                    "status": r.getcode() or 200,
                    "dns_error": False,
                    "ssl_error": False,
                    "invalid_response": False,
                }
            ]

            mime_type = get_mime_type(content, url)
            encoding = get_encoding(content)

            content_type = get_content_type(mime_type, encoding)
            content = decode_content(content, mime_type, encoding)
    except Exception as err:
        match = FTP_STATUS_PATTERN.search(repr(err))

        status = None if match is None else int(match.group(1))
        status = 408 if status == 115 else status  # FTP timeout

        redirects = [
            {
                "url": url,
                "ip_port": None,
                "response_time": None,
                "status": status,
                "dns_error": status == 434,
                "ssl_error": False,
                "invalid_response": True,
            }
        ]

        content = None
        content_type = None

    return (request_date, redirects, content, content_type)
