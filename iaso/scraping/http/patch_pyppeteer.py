# Pyppeteer Chromium download path (for MacOS)
#
# Published by Peter Zagubisalo under the MIT License:
# https://github.com/kiwi0fruit/pyppdf/blob/master/pyppdf/patch_pyppeteer/patch_pyppeteer.py

import certifi
from pyppeteer.chromium_downloader import *


NO_PROGRESS_BAR = os.environ.get("PYPPETEER_NO_PROGRESS_BAR", "")
if NO_PROGRESS_BAR.lower() in ("1", "true"):
    NO_PROGRESS_BAR = True  # type: ignore

win_postf = "win" if int(REVISION) > 591479 else "win32"
downloadURLs.update(
    {
        "win32": f"{BASE_URL}/Win/{REVISION}/chrome-{win_postf}.zip",
        "win64": f"{BASE_URL}/Win_x64/{REVISION}/chrome-{win_postf}.zip",
    }
)
chromiumExecutable.update(
    {
        "win32": DOWNLOADS_FOLDER / REVISION / f"chrome-{win_postf}" / "chrome.exe",
        "win64": DOWNLOADS_FOLDER / REVISION / f"chrome-{win_postf}" / "chrome.exe",
    }
)


def download_zip(url: str) -> BytesIO:
    """Download data from url."""
    logger.warning(
        "start patched secure https chromium download.\n"
        "Download may take a few minutes."
    )

    with urllib3.PoolManager(
        cert_reqs="CERT_REQUIRED", ca_certs=certifi.where()
    ) as https:
        # Get data from url.
        # set preload_content=False means using stream later.
        data = https.request("GET", url, preload_content=False)

        try:
            total_length = int(data.headers["content-length"])
        except (KeyError, ValueError, AttributeError):
            total_length = 0

        process_bar = tqdm(
            total=total_length,
            file=os.devnull if NO_PROGRESS_BAR else None,
        )

        # 10 * 1024
        _data = BytesIO()
        for chunk in data.stream(10240):
            _data.write(chunk)
            process_bar.update(len(chunk))
        process_bar.close()

    logger.warning("\nchromium download done.")

    return _data


def patch_pyppeteer():
    import pyppeteer.chromium_downloader
    import pyppeteer.connection
    import pyppeteer.launcher

    pyppeteer.chromium_downloader.download_zip = download_zip

    original_connect = pyppeteer.connection.websockets.client.connect

    def new_connect(*args, **kwargs):
        kwargs["ping_interval"] = None
        kwargs["ping_timeout"] = None

        return original_connect(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_connect

    if "--disable-features=site-per-process" in pyppeteer.launcher.DEFAULT_ARGS:
        pyppeteer.launcher.DEFAULT_ARGS.remove("--disable-features=site-per-process")
