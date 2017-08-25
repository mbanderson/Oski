#!/usr/bin/env python
"""Saves web articles as pdfs."""

import argparse
import pdfkit
import signal
from functools import wraps


def timeout(secs=20):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(secs)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0) # disable alarm
            return result

    def handler():  return

    return decorator


@timeout
def save_article(url, title):
    """Save url as a pdf."""
    options = {'quiet': ''}
    try:
        # If wkhtmltopdf.exe not on path, add configuration:
        # config = pdfkit.configuration(wkhtmltopdf="path/to/wkhtmltopdf")
        # pdfkit.from_url(..., configuration=config)

        success = pdfkit.from_url(url, title + '.pdf', options=options)
        return True
    except IOError:  return False
    

def main(args):
    return save_article(args.url, args.title)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, required=True,
        help="specify url to save as article")
    parser.add_argument("--title", type=str, required=True,
        help="specify article title")
    args = parser.parse_args()

    main(args)