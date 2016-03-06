.. Blogit documentation master file, created by
   sphinx-quickstart on Wed Feb 17 16:38:24 2016.
   You can adapt this file completely to your liking,
   but it should at least
   contain the root `toctree` directive.

Welcome to blogit's documentation!
==================================

About blogit:
^^^^^^^^^^^^^

Blogit is a Python3 static site generator. It uses the markdown2 parser,
and the Jinja2 template engine. It is a small code base, and does
gradual builds of your content. Thus it is quick! New posts are added by
demand, without the need to reparse and  rebuild all the content every
time.

Oh no, why another static site generator?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Well, I looked into a few of them already a couple of years ago, and non
made me happy. I wanted a tool written in Python so I could read the code
and improve it. But, the ones I looked into where simply to big to just do
what I needed - a simple and fast static site generator.

Take a look for example at nikola, which has ~14,000 lines of code(!), or
Pelican, which is smaller, but still has ~7600 lines of code. One of the mostly
used static site generator, jekyll is written in Ruby, and has only a mere ~4800
lines of code [#]_.

Blogit, does all what they do, with a hubmle ~320 lines of code, in beatiful
Python. A simple code, which is simply a wrapper around Jinja2 and
Markdown. That is Unixy. It does not invent it's own template language, rather
it uses the really good and established Jinja2 template engine. It does not
include it's own markdown parser, it uses the excellent, feature rich and speedy
markdown2 parser.

It sticks to the following philosophy - less code equals less bugs.

Installing
^^^^^^^^^^

You can obtain blogit using pip::

  $ pip3 install blogit


Getting started
^^^^^^^^^^^^^^^

To use blogit you should create an empty directory contating a simple
configuration file ``conf.py``, the file has the following content for a start::


        CONFIG = {
            'content_root': 'content',  # where the markdown files are
            'output_to': '.',
            'templates': 'templates',
            'http_port': 3030,
            'content_encoding': 'utf-8',
            'author': 'Oz Nahum Tiram',
            'ARCHIVE_SIZE': 10,
            'INDEX_SIZE': 10
            }

        GLOBAL_TEMPLATE_CONTEXT = {
            'media_base': '/media/',
            'media_url': '../media/',
            'site_url': 'http://oz123.github.com',
        }

And that is it. It's pretty clear what you need to customize here for your own
needs.  Blogit configuration is a Python module, with two dictionaries. You
don't to be a Python expert to modify this file. This is not the only project
that chooses this configuration style. Other well known projects,
like sphinx or django, chose Python code as a configuration language,
instead of choosing the ini, yaml formats or what ever DSL for configuration.

Next, you need to create some Jinja templates inside the templates directory
and some markdown files inside the content directory. When you are done, you
can build your blog with::

    $ blogit -b

You can preview the HTML generated files using::

    $ blogit -p

And that is all in a quick way. To learn more, your probably need to know
some Jinja2 and maybe some HTML to get a good looking website. Alas, you can
use the existing example `blogit-mir` theme to quickly get started. To use this
theme there is the `quick-start` option, just create a directory where you want
your files to exist and issue::

    $ blogit --quick-start

This command will create in your directory the following structure::

        .
        ├── conf.py
        ├── content
        │   ├── pages
        │   │   └── about.md
        │   └── posts
        │       ├── 1865-11-26-down-the-rabbit-hole.md
        │       ├── 1871-03-18-looking-glass-house.md
        │       ├── 1912-07-24-out-to-sea.md
        │       ├── 1948-12-12-the-purpose-of-education.md
        │       ├── 1963-08-28-i-have-a-dream.md
        │       └── 2014-08-12-the-businessman-and-fisherman.md
        ├── media
        │   ├── css
        │   │   ├── bootstrap.min.css
        │   │   ├── bootstrap-theme.min.css
        │   │   ├── print.css
        │   │   ├── pygments_style.css
        │   │   ├── site.css
        │   │   ├── style.css
        │   │   └── tipsy.css
        │   ├── img
        │   │   ├── about.png
        │   │   ├── body_bg.png
        │   │   ├── code_top_bg.png
        │   │   ├── flickr.png
        │   │   ├── github.png
        │   │   ├── g+.png
        │   │   ├── home.png
        │   │   ├── in.png
        │   │   ├── noise.png
        │   │   ├── rss.png
        │   │   └── twitter.png
        │   └── js
        │       ├── bootstrap.min.js
        │       ├── googlefonts.js
        │       ├── highlight.pack.js
        │       ├── jquery.js
        │       ├── jquery.min.js
        │       ├── jquery.tipsy.js
        │       └── scripts.js
        ├── __pycache__
        │   └── conf.cpython-35.pyc
        ├── README.md
        └── templates
            ├── about.html
            ├── archive_index.html
            ├── atom.xml
            ├── base.html
            ├── discuss.html
            ├── entry.html
            ├── entry_index.html
            ├── explorer.html
            ├── google_analytics.html
            ├── sidebar.html
            └── tag_index.html

        9 directories, 46 files

You can now build the example blog and start the demo webserver in one command::

    $ blogit -bp
    Rendering website now...
    entries:
    posts/1963-08-28-i-have-a-dream.md
    posts/2014-08-12-the-businessman-and-fisherman.md
    posts/1948-12-12-the-purpose-of-education.md
    posts/1912-07-24-out-to-sea.md
    posts/1865-11-26-down-the-rabbit-hole.md
    pages/about.md
    updating tag speeches
    updating tag  fiction
    updating tag fiction
    updating tag fables
    Updating index
    Updating archive
    and ready to test at http://127.0.0.1:3030
    Hit Ctrl+C to exit

The next time you will add a new post **only** that post will be build. Other,
pages that will be updated are the posts tags, the archive and the main index.
Everything else remains unchanged. Hence, the speed up in build times.

There is only one caveat for the way blogit does gradual builds. Currently,
once a post is built it is stored in the file ``content_root/blogit.db`` and
it is not built again. Future versions of blogit will store also the last
modification time of the file and will build the file if the change time is
newer then the one stored in the database.

If you can't wait until than, you can modify the database, or completely remove
it. Modifying the database is straight forward. It's a simple JSON file. Just
make sure you don't forget to close curly brackets when you edit the file.

Contributing
^^^^^^^^^^^^

Bug reports and pull requests are most welcome in https://github.com/oz123/blogit.
If you happen to create a new theme you can also submit it. Porting jekyll themes
isn't that hard too.




.. rubric:: Footnotes

.. [#] generated using David A. Wheeler's 'SLOCCount'.
