#!/usr/bin/env python
"""Saves web articles as pdfs."""

import argparse
import pdfkit
import signal
import os
import errno
from functools import wraps


class TimeoutError(Exception):
    pass

def timeout(secs=60, default=False):
    def decorator(func):
        def handler(signum, frame):
            msg = os.strerror(errno.ETIME)
            raise TimeoutError(msg)

        @wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(secs)
            try:
                result = func(*args, **kwargs)
            except TimeoutError:
                result = default
            finally:
                signal.alarm(0) # disable alarm
            return result

        return wrapper

    return decorator


@timeout()
def save_article(url, title, path=""):
    """Save url as a pdf."""
    options = {'quiet': ''}
    try:
        # If wkhtmltopdf.exe not on path, add configuration:
        # config = pdfkit.configuration(wkhtmltopdf="path/to/wkhtmltopdf")
        # pdfkit.from_url(..., configuration=config)
        output_path = path + os.sep + title + '.pdf'
        pdfkit.from_url(url, output_path, options=options)
        return True
    except IOError:  return False
    

def main(args):
    return save_article(args.url, args.title, args.path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, required=True,
        help="specify url to save as article")
    parser.add_argument("--title", type=str, required=True,
        help="specify article title")
    parser.add_argument("--path", type=str,
        help="specify output directory path")
    args = parser.parse_args()

    if args.path and not os.path.isdir(args.path):
        os.makedirs(args.path)

    main(args)