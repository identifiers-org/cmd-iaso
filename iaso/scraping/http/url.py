from urllib.parse import urldefrag


def normaliseURL(url):
    url = urldefrag(url).url

    return url[:-1] if url.endswith("/") else url
