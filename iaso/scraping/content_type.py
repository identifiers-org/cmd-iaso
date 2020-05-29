import base64

import chardet
import puremagic


def patch_puremagic():
    def _confidence(matches, ext=None):
        """ Rough confidence based on string length and file extension"""
        results = []
        for match in matches:
            con = (
                0.8
                if len(match.extension) >= 8
                else float("0.{0}".format(len(match.extension)))
            )
            if ext == match.extension:
                con = 0.9
            results.append(
                puremagic.main.PureMagicWithConfidence(
                    confidence=con, **match._asdict()
                )
            )
        return sorted(results, key=lambda x: x.confidence, reverse=True)

    puremagic.main._confidence = _confidence


patch_puremagic()


def get_mime_type(content, url):
    return puremagic.from_string(
        content, mime=True, filename=os.path.basename(urlparse(url).path)
    )


def get_encoding(content):
    return chardet.detect(content)["encoding"] or "binary"


def get_content_type(mime_type, encoding):
    return f"{mime_type}; charset={encoding}"


def decode_content(content, mime_type, encoding):
    if encoding == "binary":
        return "data:{};base64,{}".format(
            mime_type, base64.b64encode(content).decode("utf-8")
        )
    else:
        return content.decode(encoding)
