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
use the existing example `blogit-mir` theme to quickly get started.

.. rubric:: Footnotes

.. [#] generated using David A. Wheeler's 'SLOCCount'.
