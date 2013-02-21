"""
Static site generator.

Copyright (c) 2009 Liam Cooke
Licensed under the terms of the MIT license.

"""
import commands
import os
import re
import sys
import time
from itertools import izip

import dateutil.parser

# We need a timezone... but there's no point pulling in the whole of pytz
from datetime import datetime, tzinfo, timedelta

class utc(tzinfo):
    def tzname(self, dt): return "UTC"
    def dst(self, dt): return timedelta(0)
    def utcoffset(self, dt): return timedelta(0)

def die(*msg):
    sys.stderr.write(' '.join(str(m) for m in msg) + '\n')
    sys.exit(1)

def run_or_die(cmd):
    status, output = commands.getstatusoutput(cmd)
    if status > 0: die(output)


alphanum = lambda s: re.sub('[^A-Za-z0-9]', '', s)
filemtime = lambda f: datetime.fromtimestamp(os.fstat(f.fileno()).st_mtime)
identity = lambda o: o
is_str = lambda o: isinstance(o, basestring)
timestamp = lambda dt: dt and int(time.mktime(dt.timetuple())) or 0


norm_key = lambda s: re.sub('[- ]+', '_', s.lower())
norm_time = lambda s: s and dateutil.parser.parse(str(s), fuzzy=True).replace(tzinfo=utc()) or None

def norm_tags(obj):
    tags = is_str(obj) and obj.split(',' in obj and ',' or None) or obj
    return set(filter(bool, (alphanum(tag) for tag in tags)))


def mkdir(d):
    try: os.makedirs(d)
    except OSError: pass

def neighbours(iterable):
    "1..4 -> (None,1,2), (1,2,3), (2,3,4), (3,4,None)"
    L = list(iterable)
    a = [None] + L[:-1]
    b = L[1:] + [None]
    return izip(a, L, b)
