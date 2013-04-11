JILCROW
=======

A static site generator, tailored for *my* own needs. (Work in progress.)

Use It
------

    mkdir mysite
    cd mysite
    mkvirtualenv mysite
    pip install -e hg+http://bitbucket.org/sjl/jilcrow/#egg=jilcrow

    ... make your folders ...

    jilcrow .

Structure
---------

    mysite/
        content/
            ... content files, like blog entries and flat pages ...
        files/
            ... miscellaneous files, will be copied directly into deploy/ ...
        templates/
            ... site templates ...
        deploy/
            ... where jilcrow puts the resulting files ...
        site.cfg
            ... INI style config file for your jilcrow site ...

Etc
---

Licensed under the terms of the MIT license (see the LICENSE file).
