import base64
import itertools
import re

import eml_parser

from bs4 import BeautifulSoup

CONTAINS_CID = re.compile(r'(?:src="cid:[^"]+")|(?:href="cid:[^"]+")')
CID = re.compile(r"^cid:(.+)$")


def substitute_xml(content, contents):
    if isinstance(content, bytes):
        content = base64.b64decode(content).decode("utf-8", "ignore")

    soup = BeautifulSoup(content, "lxml")

    if CONTAINS_CID.search(content) is None:
        return soup

    # Fill in the tag contents where a tag links to a content with a cid
    for tag, attr in itertools.chain(
        ((tag, "src") for tag in soup.find_all(src=CID)),
        ((tag, "href") for tag in soup.find_all(href=CID)),
    ):
        cid = CID.match(tag.attrs[attr]).group(1)

        inner_content = contents.get(f"<{cid}>")

        if inner_content is None:
            continue

        inner_content = substitute_xml(inner_content, contents)

        tag.append(inner_content)

    return soup


def substitute_outer(content, contents):
    if isinstance(content, bytes):
        content = base64.b64decode(content).decode("utf-8", "ignore")

    # Check if the content contains a cid - if not we assume it is a string here
    if CONTAINS_CID.search(content) is None:
        return content

    # From here on we assume the content is valid XML
    return str(substitute_xml(content, contents))


async def fetch_html_content(page):
    snapshot = await page._client.send("Page.captureSnapshot")

    eml = eml_parser.EmlParser(
        include_raw_body=True, parse_attachments=True, include_attachment_data=True
    ).decode_email_bytes(snapshot["data"].encode("utf-8", "ignore"))

    # Find the contents of all attachments and body parts
    contents = dict(
        itertools.chain(
            (
                (attachment["content_header"]["content-id"][0], attachment["raw"])
                for attachment in eml.get("attachment", [])
                if "content-id" in attachment["content_header"]
            ),
            (
                (body["content_header"]["content-id"][0], body["content"])
                for body in eml.get("body", [])
                if "content-id" in body["content_header"]
            ),
        )
    )

    # Find the root document
    root_content = next(
        itertools.chain(
            (
                body["content"]
                for body in eml.get("body", [])
                if body["content_header"]["content-location"][0]
                == eml["header"]["header"]["snapshot-content-location"][0]
            ),
            (
                attachment["raw"]
                for attachment in eml.get("attachment", [])
                if attachment["content_header"]["content-location"][0]
                == eml["header"]["header"]["snapshot-content-location"][0]
            ),
        )
    )

    return substitute_outer(root_content, contents)
