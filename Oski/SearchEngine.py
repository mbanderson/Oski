#!/usr/bin/env python
"""Searches for articles using the Google Custom Search API."""

import argparse
import json
import os
import sys
from pprint import pprint
from googleapiclient.discovery import build


def to_ascii(text):
    """Convert text input to ascii."""
    return text.encode('ascii', errors='ignore')

def read_engine_json(json_file, key_str):
    """Read value of key_str in json_file."""
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            content = json.load(f)
            try:
                return content[key_str]
            except KeyError:  pass
    return ""


class SearchEngine:
    """Queries Google API for article results."""
    SINGLE_QUERY_MAX_RES = 10
    MULTI_QUERY_MAX_RES = 100

    def __init__(self, dev_key, engine_id):
        # Custom search engine defined in Google Dev Console
        self.engine_id = engine_id
        # Service for Google API Console
        self.service = build("customsearch", "v1", developerKey=dev_key)

    def query(self, search_str, num_results):
        """Query engine with search string, leaf through multiple pages."""
        results = []
        page_start = 1
        res_to_go = min(num_results, self.MULTI_QUERY_MAX_RES)

        while (res_to_go > 0):
            # Query results from current page
            num_query = min(res_to_go, self.SINGLE_QUERY_MAX_RES)
            content = self.service.cse().list(q=search_str, 
                                              cx=self.engine_id,
                                              num=num_query,
                                              start=page_start).execute()
            # Check if out of results
            if "items" not in content.keys():  break
            
            # Add results and move to next page
            res_to_go -= len(content["items"])
            results += content["items"]
            try:
                page_start = content["queries"]["nextPage"][0]["startIndex"]
            except KeyError:  break

        return [SearchResult(res) for res in results]

    def __repr__(self):
        return self.engine_id


class SearchResult:
    """Extracts and stores relevant content from search result."""
    def __init__(self, api_result):
        self.title = to_ascii(api_result["title"])
        self.url = to_ascii(api_result["link"])
        self.snippet = to_ascii(api_result["snippet"])

    def __repr__(self):
        return self.title
    

def main(args):
    """Run input query in search engine."""
    engine = SearchEngine(args.dev_key, args.engine_id)
    results = engine.query(args.query, args.results)
    pprint(results)
    print "Found %d results." % len(results)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-kf", "--keyfile", type=str, required=True,
                        help="specify file containing Google API key")
    parser.add_argument("-ef", "--enginefile", type=str, required=True,
                        help="specify file containing search engine parameters")
    parser.add_argument("-q", "--query", type=str, default="Cal Kicker",
                        help="specify search query")
    parser.add_argument("-r", "--results", type=int, default=10,
                        help="specify number of results")
    args = parser.parse_args()

    args.dev_key = read_engine_json(args.keyfile, "dev_key")
    args.engine_id = read_engine_json(args.enginefile, "engine_id")
    if args.dev_key and args.engine_id:
        main(args)
    else:
        print "SearchEngine: Not able to read input key files."
        sys.exit(1)