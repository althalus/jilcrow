"""
Static site generator.

Copyright (c) 2009 Liam Cooke
Licensed under the terms of the MIT license.

"""
import sys
if sys.version_info < (2, 6) or sys.version_info >= (3, 0):
    msg = "only Python 2.6 is supported at the moment"
    raise ImportError(msg)

import shutil
import os
import locale
locale.setlocale(locale.LC_ALL, '')

from jilcrow.core import Jilcrow


__author__ = 'Liam Cooke'
__copyright__ = 'Copyright (c) 2009 Liam Cooke'
__license__ = 'MIT License'


def main():
    import optparse
    parser = optparse.OptionParser('usage: %prog [options] path_to_site')
    parser.add_option('-x', '--clean', action='store_true', default=False)
    parser.add_option('-t', '--test', action='store_true', default=False,
                      help='open the site in your browser after building')
    parser.add_option('-i','--init',action='store_true',default=False,
                      help='Initialise layout and templates for a new site at path_to_site')
    options, args = parser.parse_args()

    if args:
        site_path = args.pop(0)
    else:
        parser.print_help()
        return 1


    if options.init:
        datadir = os.path.join(os.path.dirname(__file__),"samplesite")
        try:
            shutil.copytree(datadir, site_path)
        except Exception, e:
            print "Couldn't initiate site: %s" % e
    else:
        site = Jilcrow(site_path)
        site.build(clean=options.clean)

    if options.test:
        import webbrowser
        url = site.join_url(site.get('test_domain', 'http://localhost/'),
                            site.get('test_root', site['root']), ext=False)
        webbrowser.open_new_tab(url)
