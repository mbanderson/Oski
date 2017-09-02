#!/usr/bin/env python
"""Oski is the figurehead (read: mascot) of the full archiver pipeline."""

import argparse
import json
import jsonschema
import sys
import os
from SearchEngine import (SearchEngine, read_engine_json, 
                          read_banned_domains, rem_banned_domains, to_ascii)
from ArticleDB import Article, ArticleDB, create_articles
from Archiver import save_article
from Notifier import Notifier, Email
from datetime import datetime


class Oski:
    """Manages searching, archiving, storing in database, and notifying."""
    def __init__(self, oski_json, keys, notif_json=""):
        # Validate json
        [success, params] = load_json(oski_json)
        if not success:
            sys.exit(1)

        # Load parameters
        self.queries = params["searcher"]["queries"]

        # Read banned domains parameter
        self.banned_domains = None
        if "ban_file" in params["searcher"].keys():
            ban_file = params["searcher"]["ban_file"]
            if os.path.exists(ban_file):
                self.banned_domains = read_banned_domains(ban_file)
            else:
                print "Oski: Unable to LOCATE %s" % ban_file

        # Initialize search engine and database
        self.searcher = SearchEngine(keys["dev_key"], keys["engine_id"])
        self.db = ArticleDB()

        # Optionally, initialize archiving system
        self.save_pdfs, self.save_path = None, None
        if "archiver" in params.keys():
            self.save_pdfs = params["archiver"]["save_pdfs"]
            self.save_path = params["archiver"]["save_path"]

        # Optionally, notify subscribers of new articles
        self.notifier = None
        if notif_json:
            subscr_file = notif_json["subscr_file"]
            if os.path.exists(subscr_file):
                with open(subscr_file, 'r') as f:
                    subscribers = f.readlines()
                self.notifier = Notifier(subscribers, 
                                         notif_json["user"], notif_json["pwd"])
            else:
                print "Oski: Unable to LOCATE %s" % subscr_file


    def oski_update(self, articles):
        """Add to database, make pdfs, update subscribers."""
        # Try to add to db
        added = self.db.add_articles(articles)
        print "Found %d new articles" % len(added)

        # Email subscribers about new articles
        if added and self.notifier:
            subject = "New Articles!"
            html = create_email_html(added)
            if html:
                email = Email(self.notifier.user,
                            "", subject, html, use_html=True)
                self.notifier.mail_subscribers(email) 
                print "Mailed subscribers! %s" % str(datetime.now())

        # Convert added articles to pdfs
        if added and self.save_pdfs:
            for search_res in added:
                try:
                    success = save_article(search_res.url, 
                                           search_res.title, self.save_path)
                    if success:
                        print 'Oski: Saved article "%s"' % search_res.title
                    else:  
                        print 'Oski: Save TIMEOUT on "%s"' % search_res.title
                except Exception as e:
                    print 'Oski: Non-timeout EXCEPTION on "%s"' % search_res.title
                    print e

        return added

    def perform_search(self, init_search=True):
        """Search for content with each input query."""
        results = []
        for query in self.queries:
            search = query["search"]

            if init_search:
                num_results = query["num_results"]["init"]
            else:
                num_results = get_value(query["num_results"], "update", 10)

            exact_terms, or_terms, date_restrict = "", "", ""
            if "options" in query.keys():
                exact_terms = get_value(query["options"], "exact_terms")
                or_terms = get_value(query["options"], "or_terms")
                date_restrict = get_value(query["options"], "date_restrict")

            # Hunt for recent articles
            results += self.searcher.query(search, num_results, 
                                           exact_terms, or_terms, date_restrict)
        
        results = rem_banned_domains(results, self.banned_domains)
        return create_articles(results)

    def initial_search(self):
        """Searches for content without date restrictions.
        This is to perform the initial database population.
        """
        return self.perform_search(init_search=True)

    def recent_search(self):
        """Searches for recent content, with date restrictions."""
        return self.perform_search(init_search=False)


def create_email_html(articles, 
                      header_html="EmailTemplates/CalBearsHeader.html", 
                      article_html="EmailTemplates/CalBearsArticle.html"):
    html = ""
    if not check_files_exist([header_html, article_html]) or len(articles) == 0:  
        return html
    with open(header_html, 'r') as f:
        header_template = f.read()
    with open(article_html, 'r') as f:
        article_template = f.read()

    html += '<table style="width: 600px">'
    html += header_template
    for article in articles:
        html += article_template.format(article.url, article.title, 
                                        article.snippet)
    html += "</table>"
    html = html.replace("\n", "")
    return html

## Helpers
def check_files_exist(files):
    """Check all files in input list exist."""
    for input_file in files:
        if not os.path.exists(input_file):
            print "Oski: Unable to LOCATE %s" % input_file
            return False
    return True

def uni2ascii(input):
    """Recursively convert all unicode values to ascii."""
    if isinstance(input, dict):
        return dict((uni2ascii(key), uni2ascii(value)) \
                     for key, value in input.iteritems())
    elif isinstance(input, list):
        return [uni2ascii(element) for element in input]
    elif isinstance(input, unicode):
        return to_ascii(input)
    else:
        return input

def validate(json_file, schema):
    """Validate input json file against schema json file."""
    if not check_files_exist([json_file, schema]):
        return False, None
    with open(json_file, 'r') as f:
        content = json.load(f)
    with open(schema, 'r') as f:
        schema = json.load(f)
    try:
        jsonschema.validate(content, schema)
        return True, content
    except (jsonschema.exceptions.ValidationError,
            jsonschema.exceptions.SchemaError):
        print "Oski: Validation test FAILED on %s" % json_file
        return False, None

def load_json(json_file, schema="Schema/OskiSchema.json"):
    """Validate json file and convert unicode values to ascii."""
    [success, params] = validate(json_file, schema)
    if success:
        params = uni2ascii(params)
    return success, params

def get_value(json_dict, key, default=""):
    """Try to fetch optional parameters from input json dict."""
    try:
        return json_dict[key]
    except KeyError:  return default


def main(args):
    # Determine if database previously populated
    do_init_searches = not os.path.exists(ArticleDB.DB_NAME)

    # Hire Oski
    oski = Oski(args.oskifile, args.keys, args.notifyparams)
        
    # Search for articles
    if do_init_searches:
        new_articles = oski.initial_search()
    else:
        new_articles = oski.recent_search()

    # Add to datebase and notify
    oski.oski_update(new_articles)
    
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-op", "--oskifile", type=str, required=True,
        help="specify parameter file for Oski")
    parser.add_argument("-kf", "--keyfile", type=str, required=True,
        help="specify file containing search engine keys")
    parser.add_argument("-np", "--notifyfile", type=str,
        help="specify file containing email notification parameters")
    args = parser.parse_args()

    if not check_files_exist([args.oskifile, args.keyfile]):
        print "Oski: Unable to LOCATE input parameter or key files."
        sys.exit(1)
    if args.notifyfile and not os.path.exists(args.notifyfile):
        print "Oski: Notification settings provided but unable to LOCATE file."

    with open(args.keyfile, 'r') as f:
        args.keys = json.load(f)
    with open(args.notifyfile, 'r') as f:
        args.notifyparams = json.load(f)

    main(args)