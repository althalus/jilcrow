"""
Static site generator.

Copyright (c) 2009 Liam Cooke
Licensed under the terms of the MIT license.

"""
import codecs
import locale
import os
import re
import shutil
from collections import defaultdict
from os import path

import PyRSS2Gen as rss2
import yaml
from jinja2 import Environment, FileSystemLoader

from jilcrow import pages, util

# We need a timezone... but there's no point pulling in the whole of pytz
from datetime import datetime, tzinfo, timedelta

class utc(tzinfo):
    def tzname(self, dt): return "UTC"
    def dst(self, dt): return timedelta(0)
    def utcoffset(self, dt): return timedelta(0)
 



DEFAULT_CONFIG_FILE = 'site.yml'
DEFAULT_CONFIG = {
    'domain': 'http://localhost/',
    'root': '/',
    'clean_urls': False,
    'content_extensions': ('text', 'markdown', 'mkdn', 'md'),
    'dirs': {
        'content': 'content',
        'files': 'files',
        'templates': 'templates',
        'deploy': 'deploy',
    },
    'feed': 'feed.rss',
    'files_exclude': r'^[\._]|~$',
    'files_include': r'^\.htaccess$',
    'files_rename': {
        '.less': '.css',
    },
    'lang': 'en',
}


class PageDatabase:
    tags_by_count = lambda self: sorted(self.tags.values(), key=pages.Tag.sortkey_count)
    tags_by_name = lambda self: sorted(self.tags.values(), key=pages.Tag.sortkey_tag)

    def __init__(self, site):
        self._site = site
        self.pages, self.tags = {}, {}
        tdir = self._site['dirs']['templates']
        self.env = Environment(loader=FileSystemLoader(tdir))

    def __getitem__(self, id):
        return self.pages[id]

    def __iter__(self):
        return iter(self.pages.values())

    def add(self, page):
        if page.id in self.pages:
            util.die('duplicate page id: %s' % page.id)
        self.pages[page.id] = page

        if type(page) is pages.Tag:
            self.tags[page.name] = page
        elif 'tags' in page:
            page_tags = {}
            for tag_name in page.get('tags', []):
                if tag_name in self.tags:
                    tag = self.tags[tag_name]
                else:
                    tag = pages.Tag(self._site, tag_name)
                    self.add(tag)
                tag.add(page)
                page_tags[tag_name] = tag
            page['tags'] = page_tags

    def select(self, limit=None, dated=True, tag=None, chrono=False, sortby_origin=None):
        if sortby_origin is None:
            sortby_origin = bool(chrono)
        sortkey = sortby_origin and pages.Page.sortkey_origin or pages.Page.sortkey_posted
        results = sorted(self.pages.values(), key=sortkey, reverse=not chrono)
        if dated:
            results = [page for page in results if page.date]
            if tag:
                results = [page for page in results if tag in page.tags]
        return tuple(results)[:limit]

    def render(self):
        for page in self:
            t = page.template or self._site['default_template']
            template = self.env.get_template('%s.html' % t)
            print('%14s : /%s' % (t, page.id))

            vars = dict(self._site, **page)

            vars['len'] = len
            vars['enumerate'] = enumerate
            vars['all_tags'] = self.tags_by_count

            if vars['title']:
                vars['head_title'] = vars['title_format'] % vars

            if page.id.endswith('/index'):
                loc = page.id.rsplit('/', 1)[0]
                vars['pages'] = [p for p in self
                                 if p.id.startswith(loc) and not p.id == page.id]

            html = template.render(**vars).strip()
            fname = path.join(self._site['dirs']['deploy'], page.path())
            with open(fname, 'w') as f:
                f.write(html.encode('utf-8'))


class Jilcrow(dict):
    FILES_ACTIONS = {
        '.less': lambda s, d: util.run_or_die('lessc %s %s' % (s, d)),
    }

    def __init__(self, site_path, config_file=DEFAULT_CONFIG_FILE):
        try: os.chdir(site_path)
        except OSError: util.die('invalid path:', site_path)
        if not path.exists(config_file):
            util.die('%s not found' % config_file)

        dict.__init__(self, DEFAULT_CONFIG)
        self.update(locale.localeconv())
        with open(config_file) as f:
            for k, v in yaml.load(f).items():
                k = util.norm_key(k)
                if type(v) is dict:
                    self[k] = dict(self.get(k, {}), **v)
                else:
                    self[k] = v

    def join_url(self, *parts, **kwargs):
        ext = (kwargs.get('ext', 1) and not self['clean_urls']) and '.html' or ''
        url = re.sub('//+', '/', '/'.join(str(s) for s in parts if s))
        if ext and url.endswith(ext):
            url = url[:-len(ext)]
        return url + ext

    def join_path(self, id):
        deploy_path = path.realpath(self['dirs']['deploy'])
        if self['clean_urls'] and not id.endswith("index"):
            return path.join(deploy_path, id, 'index.html')
        else:
            return path.join(deploy_path, "%s.html" % id)

    def build(self, clean=False):
        base_path = path.realpath(os.curdir)
        deploy_path = path.realpath(self['dirs']['deploy'])
        if clean:
            shutil.rmtree(deploy_path, ignore_errors=True)
            util.mkdir(deploy_path)

        os.chdir(self['dirs']['files'])
        excludes, includes = re.compile(self['files_exclude']), re.compile(self['files_include'])
        for root, _, files in os.walk(os.curdir):
            util.mkdir(path.normpath(path.join(deploy_path, root)))
            for fname in files:
                if excludes.match(fname) and not includes.match(fname):
                    continue
                src, dest = path.join(root, fname), path.join(deploy_path, root, fname)
                ext = path.splitext(fname)[1]
                if ext in self['files_rename']:
                    dest = path.splitext(dest)[0] + self['files_rename'][ext]
                if path.isfile(dest) and path.getmtime(src) <= path.getmtime(dest):
                    continue
                self.FILES_ACTIONS.get(ext, shutil.copy2)(src, dest)
                print('{0} => {1}'.format(path.relpath(src, base_path), path.relpath(dest, base_path)))
        os.chdir(base_path)

        db, years = PageDatabase(self), defaultdict(lambda: defaultdict(list))
        for root, _, files in os.walk(self['dirs']['content']):
            exts = ['.%s' % ext for ext in self['content_extensions']]
            now = datetime.now().replace(tzinfo=utc())
            for file in [f for f in files if path.splitext(f)[1] in exts]:
                with codecs.open(path.join(root, file), 'r', encoding='utf-8') as fp:
                    page = pages.Content(self, fp)
                    if page.date:
                        if page.posted:
                            posted = page.posted.tzinfo and page.posted \
                                    or page.posted.replace(tzinfo=utc())
                            if posted < now:
                                db.add(page)
                                years[posted.year][posted.month].append(page)
                        else:
                            db.add(page)
                            years[page.date.year][page.date.month].append(page)

        for year, months in years.items():
            month_pages = []
            for month, posts in sorted(months.items()):
                posts = sorted(posts, key=pages.Page.sortkey_origin)
                m = pages.Month(self, posts, year, month)
                db.add(m)
                month_pages.append(m)
            db.add(pages.Year(self, month_pages, year))
        for prevpost, post, nextpost in util.neighbours(db.select(chrono=True,sortby_origin=False)):
                    post['prevpost'], post['nextpost'] = prevpost, nextpost

        if self['clean_urls']:
            dirs = [p.id for p in db]
        else:
            dirs = filter(bool, [os.path.dirname(p.id) for p in db])
        dirs = filter(lambda x: not x == "index",dirs)
        for d in sorted(set(dirs)):
            util.mkdir(os.path.join(deploy_path, d))

        self.update({
            'get': lambda id: db[str(id)],
            'get_pages': db.select,
            'domain': self['domain'].rstrip('/'),
            'root': '/' + self.get('root', '').lstrip('/'),
            'head_title': self.get('site_title', ''),
            'site_tags': db.tags,
            'join_url': self.join_url,
            'tags_by_count': db.tags_by_count,
            'tags_by_name': db.tags_by_name,
            'years': sorted(years.keys()),
            'default_template': self.get('default_template', 'page'),
        })
        self['home'] = self['domain'] + self['root']
        db.render()

        if self['feed']:
            feed_posts = db.select(10)
            feed_date = feed_posts[0].posted or feed_posts[0].date
            feed = rss2.RSS2(items=[p.feed_item() for p in feed_posts],
                title=self['site_title'], description=self.get('description', ''),
                link=self['domain'] + self['root'], generator='Jilcrow',
                language=self['lang'], lastBuildDate=feed_date)
            with open(path.join(deploy_path, self['feed']), 'w') as f:
                feed.write_xml(f, 'utf-8')
