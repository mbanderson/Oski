#!/usr/bin/env python
"""Oski is the figurehead (read: mascot) of the full archiver pipeline."""

import argparse
import json
import sys
from collections import namedtuple
from SearchEngine import (SearchEngine, read_engine_json, 
                          read_banned_domains, rem_banned_domains, to_ascii)
from ArticleDB import Article, ArticleDB, create_articles
from Archiver import save_articles
from Notifier import Notifier


class Oski:
    """Manages searching, archiving, storing in database, and notifying."""
    def __init__(self, eng_params, query_params, arch_params, notif_params):
        self.save = arch_params.save_pdfs
        self.path = arch_params.save_path

        self.query_params = query_params

        self.searcher = SearchEngine(eng_params.dev_key, eng_params.engine_id)
        self.db = ArticleDB()
        self.notifier = Notifier(notif_params.subscribers, 
                                 notif_params.notifier_user, 
                                 notif_params.notifier_pwd)

    def oski_update(self, articles):
        """Add to database, make pdfs, update subscribers."""
        # Try to add to db
        added = self.db.add_articles(articles)

        # Convert added articles to pdfs
        if added and self.save:
            for search_res in added:
                try:
                    save_article(search_res.url, search_res.title, self.path)
                except:  continue

        ## TODO: Email subscribers about new articles
        # ... Get html content
        # ... Package into email
        # ... Pass email to Notifier

        return added

    def perform_search(self, use_date_restrict=False):
        """Search for content with each input query."""
        results = []
        for i in xrange(0, len(self.query_params.queries)):
            query = self.query_params.queries[i]
            init_results = self.query_params.init_results[i]
            exact_terms = self.query_params.exact_terms[i]
            or_terms = self.query_params.or_terms[i]
            date_restrict = "" # no date restrict
            if use_date_restrict:
                date_restrict = self.query_params.date_restrict[i]

            # Hunt for recent articles
            results += self.searcher.query(query, init_results, 
                                           exact_terms, or_terms, date_restrict)
        
        results = rem_banned_domains(results, self.query_params.banned_domains)
        return create_articles(results)

    def initial_search(self):
        """Searches for content without date restrictions.
        This is to perform the initial database population.
        """
        return self.perform_search(use_date_restrict=False)

    def recent_search(self):
        """Searches for recent content, with date restrictions."""
        return self.perform_search(use_date_restrict=True)


def create_email_html(articles):
    """Create HTML content to send to subscribers."""
    pass

def set_oski_args(args):
    """Read parameters from Oski parameter file."""
    with open(args.oskiparams, 'r') as f:
        content = json.load(f)
        try:
            for key, val in content.iteritems():
                # Convert all unicode strings
                if type(val) == type(unicode()):
                    val = to_ascii(val)
                if type(val) == type(list()):
                    val = [to_ascii(v) if type(v)==type(unicode()) else v \
                           for v in val)]

                setattr(args, key, val)
        except KeyError:
            print "Oski: Not able to READ input parameter file."
            sys.exit(1)
    return

def get_engine_params(args):
    """Extract engine parameters from argparse Namespace."""
    EngineParams = namedtuple("EngineParams",
                             ["dev_key", "engine_id"])
    return EngineParams(args.dev_key, args.engine_id)

def get_query_params(args):
    """Extract query parameters from arguments."""
    QueryParams = namedtuple("QueryParams", 
                            ["queries", "init_results", "update_results",
                             "exact_terms", "or_terms", "date_restrict",
                             "banned_domains"])
    return QueryParams(args.queries, args.init_results, args.update_results,
                       args.exact_terms, args.or_terms, args.date_restrict,
                       args.banned_domains)

def get_archiver_params(args):
    """Extract archiver parameters from arguments."""
    ArchiverParams = namedtuple("ArchiverParams",
                               ["save_pdfs", "save_path"])
    return ArchiverParams(args.save_pdfs, args.save_path)

def get_notifier_params(args):
    """Extract notifier parameters from arguments."""
    NotifierParams = namedtuple("NotifierParams",
                               ["subscribers", 
                                "notifier_user", "notifier_pwd"])
    return NotifierParams(args.subscribers, 
                          args.notifier_user, args.notifier_pwd)


def main(args):
    # Determine if database previously populated
    do_init_searches = not os.path.exists(ArticleDB.DB_NAME)

    # Extract Oski parameters
    eng_params = get_engine_params(args)
    query_params = get_query_params(args)
    arch_params = get_archiver_params(args)
    notif_params = get_notifier_params(args)

    # Hire Oski
    oski = Oski(eng_params, query_params, arch_params, notif_params)
    
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
    parser.add_argument("-op", "--oskiparams", type=str, required=True,
                    help="specify parameter file for Oski")
    parser.add_argument("-ef", "--enginefile", type=str, required=True,
                    help="specify file containing search engine parameters")
    args = parser.parse_args()

    # Set parameters from Oski file
    if not os.path.exists(args.oskiparams):
        print "Oski: Not able to LOCATE input parameter file." 
    set_oski_args()

    # Read separate SearchEngine key file
    [args.dev_key, args.engine_id] = read_engine_json(
                                     args.enginefile, "dev_key", "engine_id")
    if not (args.dev_key and args.engine_id):
        print "Oski: Not able to READ input key file."
        sys.exit(1)
    
    # Load banned domains from file specified in Oski parameters
    args.banned_domains = []
    if args.banfile:
        args.banned_domains = read_banned_domains(args.banfile)

    main(args)