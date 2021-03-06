"""
Static site generator.

Copyright (c) 2009 Liam Cooke
Licensed under the terms of the MIT license.

"""
import re
import urlparse
from datetime import datetime
from os import path

import PyRSS2Gen as rss2
from BeautifulSoup import BeautifulSoup
from markdown import Markdown, markdown

from jilcrow import util


def _split_path(p):
    rest, tail = path.split(p)

    if not rest:
        return [tail]
    else:
        return _split_path(rest) + [tail]

class Page(dict):
    sortkey_origin = lambda self: (util.timestamp(self.date), self.id)
    sortkey_posted = lambda self: (util.timestamp(self.posted or self.date), self.id)

    def __init__(self, site, id, attrs={}, **kwargs):
        dict.__init__(self, {
            'content': '',
            'date': None,
            'posted': None,
            'id': str(id),
            'title': '',
            'template': '',
        })
        self._site = site
        self.update(attrs, **kwargs)

    def __getattr__(self, name):
        return self[name]

    @property
    def url(self):
        id = self.id
        return self._site.join_url(self._site['root'], id != 'index' and id)

    @property
    def full_url(self):
        return self._site['domain'] + self.url

    def path(self):
        return self._site.join_path(self.id)

class Index(Page):
    def __init__(self, site):
        super(Index, self).__init__(site, 'index', {'title':'Index','template':'home'})

class Content(Page):
    NORM = {
        'date': util.norm_time, 'posted': util.norm_time,
        'tags': util.norm_tags,
        'summary': lambda s: ''.join(BeautifulSoup(markdown(s)).findAll(text=True)),
    }
    SUMMARY = re.compile('(<summary>)(.*?)(</summary>)', re.DOTALL)

    backposted = lambda self: self.posted and self.posted.date() > self.date.date()

    def __init__(self, site, fp):
        md = Markdown(extensions= ['extra', 'meta'])
        id = path.splitext(path.join(*(_split_path(fp.name)[1:])))[0]
        Page.__init__(self, site, id, modified=util.filemtime(fp), tags=set(), summary='')
        data = fp.read()

        def _summary(m):
            summary = m.group(2).strip()
            self['summary'] = self.NORM['summary'](summary)
            return summary
        self['content'] = md.convert(self.SUMMARY.sub(_summary, data).strip())
        head = md.Meta
        if not self['summary']:
            soup = BeautifulSoup(self['content'])
            self['summary'] = soup.first('p')

        for key, val in head.items():
            key = util.norm_key(key)
            if len(val) == 1:
                val = val[0]
            try:
                self[key] = self.NORM.get(key, util.identity)(val)
            except:
                print data
        if self.date:
            self.update({
                'id': id,
                'template': self.template or 'entry',
                'month_name': self.date.strftime('%B'),
                'prevpost': None,
                'nextpost': None,
                'tags_by_count': lambda: sorted(self.tags.values(), key=Tag.sortkey_count),
                'tags_by_name': lambda: sorted(self.tags.values(), key=Tag.sortkey_tag),
            })
        if 'tags' in self._site:
            self['tags'] -= set((tag for tag in self.tags if tag not in self._site['tags']))

    def feed_item(self):
        url, title = self.full_url, self.title or 'Untitled'
        if self.backposted():
            title += ' [%s]' % self.date.strftime('%Y-%m-%d')
        tags = [rss2.Category(tag, self._site['home']) for tag in self.tags]

        content = BeautifulSoup(self.content)
        for link in content.findAll('a'):
            link['href'] = urlparse.urljoin(self.full_url, link['href'])

        return rss2.RSSItem(title=title, link=url, guid=rss2.Guid(url),
            description=str(content), pubDate=self.posted or self.date,
            categories=tags, enclosure=self.get('enclosure', None))


class Archive(Page):
    def __init__(self, site, entries, year, month, attrs={}):
        month = month and datetime(year, month, 1).strftime('%B') or ''
        id = ("archives/%s/%s" % (year, month.lower())).strip("/")
        Page.__init__(self, site, id, {
            'entries': entries,
            'year': year,
            'month': month,
            'template': 'archive_%s' % (month and 'month' or 'year'),
            'title': ("%s %s" % (month, year)).strip()
        }, **attrs)

class Month(Archive):
    def __init__(self, site, entries, year, month):
        if not (1 <= month <= 12):
            raise ValueError, 'month must be in the range 1-12'
        Archive.__init__(self, site, entries, year, month)

class Year(Archive):
    def __init__(self, site, entries, year):
        Archive.__init__(self, site, entries, year, 0)


class Tag(Page):
    sortkey_count = lambda self: (-len(self.tagged), self.name)
    sortkey_tag = lambda self: self.name

    def __init__(self, site, tag):
        id = "tags/%s" % tag
        Page.__init__(self, site, id, template='tag', tagged={})
        self.name, self['tag'] = tag, tag
        self['title'] = self._site.get('tags', {}).get(tag, tag)

    def add(self, page):
        self['tagged'][page.id] = page
