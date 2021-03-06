title: What's new in Python 2.6
date: October 1 2008
posted: 2009-12-06 22:44 UTC
tags: python, lorem ipsum

<summary>
This article (not [this article](loremipsum.html)) explains the new features in
Python 2.6, released on October 1
2008. The release schedule is described in [PEP 361][pep361].

[pep361]: http://www.python.org/dev/peps/pep-0361
</summary>

The major theme of Python 2.6 is preparing the migration path to Python 3.0, a
major redesign of the language. Whenever possible, Python 2.6 incorporates new
features and syntax from 3.0 while remaining compatible with existing code by
not removing older features or syntax. When it’s not possible to do that,
Python 2.6 tries to do what it can, adding compatibility functions in a
`future_builtins` module and a `-3` switch to warn about usages that will
become unsupported in 3.0.

Some significant new packages have been added to the standard library, such as
the `multiprocessing` and `json` modules, but there aren’t many new features
that aren’t related to Python 3.0 in some way.

Python 2.6 also sees a number of improvements and bugfixes throughout the
source. A search through the change logs finds there were 259 patches applied
and 612 bugs fixed between Python 2.5 and 2.6. Both figures are likely to be
underestimates.

This article doesn’t attempt to provide a complete specification of the new
features, but instead provides a convenient overview. For full details, you
should refer to the documentation for Python 2.6. If you want to understand
the rationale for the design and implementation, refer to the PEP for a
particular new feature. Whenever possible, “What’s New in Python” links to the
bug/patch item for each change.
