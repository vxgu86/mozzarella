"""Wiki controller module"""
import os
import tg
import pygit2 as pg

from tg import expose

from acmwebsite.lib.base import BaseController

from pygit2 import Repository,init_repository
from pygit2 import Tree
from pygit2 import Signature

from docutils.core import publish_parts


__all__ = ['WikiController']

class WikiController(BaseController):
    """Controls the wiki"""

    def __init__(self, repo, entry):
        self.repo = repo
        self.entry = entry
    
    @expose('acmwebsite.templates.wiki_view')
    def _default(self):
        """Display a specific page"""
        settings = {'initial_header_level': 2,
                    'file_insertion_enabled': 0,
                    'raw_enabled': 0,
                    'disable_config': 1,
        }

        blob = self.repo.get(self.entry.id)
        document = publish_parts(blob.data, writer_name='html5', settings_overrides=settings)
        return dict(pagename=self.entry.name.strip('.rst'), parts=document)

    @expose('acmwebsite.templates.wiki_history')
    def history(self):
        revision_list = []
        last_id = None

        #Get a list of commits that include the queried file
        for commit in self.repo.walk(self.repo.head.target, pg.GIT_SORT_TIME):
            if filename in commit.tree:
                entry = commit.tree[filename]
                if entry.id != last_id: #Only add to history if it file chnaged.
                    revision_list.append({"author": commit.author,
                                          "time": commit.commit_time,
                                          "message": commit.message})
                last_id = entry.id

        if not revision_list: #No commits include file - possibly faulty?
            tg.abort(404, "Page not found")
        return dict(page=pagename, revisions=revision_list)

class WikiPagesController(BaseController):
    def __new__(cls, repo_path=None):
        if not repo_path:
            repo_path = tg.config.get('wiki.repo')
        if not repo_path:
            return None

        obj = super().__new__(cls)
        obj.repo = Repository(repo_path)
        return obj

    @expose()
    def _lookup(self, pagename=None, *args):
        entry = None
        if pagename:
            tb = self.repo.TreeBuilder(self.repo.head.peel(Tree))
            entry = tb.get(pagename + '.rst')
        if not entry:
            tg.abort(404, "Page not found")
        return WikiController(self.repo, entry), args

    @expose()
    def index(self):
        tg.redirect('/wiki/FrontPage')

    @expose('acmwebsite.templates.wiki_pagelist')
    def pagelist(self):
        pages = [entry.name[:-4] for entry in self.repo.head.peel(Tree)]
        return dict(pages=pages)