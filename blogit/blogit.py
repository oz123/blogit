#!/usr/bin/env python
# ============================================================================
# Blogit.py is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 3
# as published by the Free Software Foundation;
#
# Blogit.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Blogit.py; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ============================================================================
# Copyright (C) 2013 Oz Nahum Tiram <nahumoz@gmail.com>
# ============================================================================

# Note about Summary
# has to be 1 line, no '\n' allowed!
"""
Summary: |
   some summary ...

Your post
"""

"""
Everything the Header can't have ":" or "..." in it, you can't have title
with ":" it makes markdown break!
"""

"""
The content directory can contain only markdown or txt files, no images
allowed!
"""
import os
import re
import datetime
import argparse
import sys
import operator
import shutil
from StringIO import StringIO
import codecs
import subprocess as sp
import SimpleHTTPServer
import BaseHTTPServer
import socket
import SocketServer
import thread

try:
    import yaml  # in debian python-yaml
    from jinja2 import Environment, FileSystemLoader  # in debian python-jinja2
except ImportError, e:  # pragma: no coverage
    print e
    print "On Debian based system you can install the dependencies with: "
    print "apt-get install python-yaml python-jinja2"
    sys.exit(1)

try:
    import markdown2
    renderer = 'md2'
except ImportError, e: # pragma: no coverage
    try:
        import markdown
        renderer = 'md1'
    except ImportError, e:
        print e
        print "try: sudo pip install markdown2"
        sys.exit(1)

import tinydb
from tinydb import Query
sys.path.insert(0, os.getcwd())
from conf import CONFIG, ARCHIVE_SIZE, GLOBAL_TEMPLATE_CONTEXT, KINDS
jinja_env = Environment(lstrip_blocks=True, trim_blocks=True,
                        loader=FileSystemLoader(CONFIG['templates']))


class DataBase(object):

    def __init__(self, path):
        _db = tinydb.TinyDB(path)
        self.posts = _db.table('posts')
        self.tags = _db.table('tags')
        self.pages = _db.table('pages')
        self.templates = _db.table('templates')
        self._db = _db

DB = DataBase(os.path.join(CONFIG['content_root'], 'blogit.db'))

class Tag(object):

    def __init__(self, name):
        self.name = name
        self.prepare()
        self.permalink = GLOBAL_TEMPLATE_CONTEXT["site_url"]
        self.table = DB.tags

        Tags = Query()
        tag = self.table.get(Tags.name == self.name)
        if not tag:
            self.table.insert({'name': self.name, 'post_ids': []})

    def prepare(self):
        _slug = self.name.lower()
        _slug = re.sub(r'[;;,. ]', '-', _slug)
        self.slug = _slug

    @property
    def posts(self):
        """
        return a list of posts tagged with Tag
        """
        Tags = Query()
        tag = self.table.get(Tags.name == self.name)
        return tag['post_ids']

    @posts.setter
    def posts(self, post_ids):
        if not isinstance(post_ids, list):
            raise ValueError("post_ids must be of type list")
        Tags = Query()
        tag = self.table.get(Tags.name == self.name)
        if not tag:  # pragma: no coverage
            raise ValueError("Tag %s not found" % self.name)
        if tag:
            new = set(post_ids) - set(tag['post_ids'])
            tag['post_ids'].extend(list(new))
            self.table.update({'post_ids': tag['post_ids']}, eids=[tag.eid])

    @property
    def entries(self):
        _entries = []
        Posts = Query()
        for id in self.posts:
            post = DB.posts.get(eid=id)
            if not post:  # pragma: no coverage
                raise ValueError("no post found for eid %s" % id)
            entry = Entry(post['filename'])
            _entries.append(entry)
        return _entries

    def render(self):
        """Render html page and atom feed"""
        self.destination = "%s/tags/%s" % (CONFIG['output_to'], self.slug)
        template = jinja_env.get_template('tag_index.html')
        try:
            os.makedirs(self.destination)
        except OSError:  # pragma: no coverage
            pass

        context = GLOBAL_TEMPLATE_CONTEXT.copy()
        context['tag'] = self
        context['entries'] = _sort_entries(self.entries)
        sorted_entries = _sort_entries(self.entries)
        encoding = CONFIG['content_encoding']
        render_to = "%s/tags/%s" % (CONFIG['output_to'], self.slug)

        jobs = [{'tname': 'tag_index.html',
                'output': codecs.open("%s/index.html" % render_to, 'w', encoding),
                'entries': sorted_entries},
                {'tname': 'atom.xml',
                 'output': codecs.open("%s/atom.xml" % render_to, 'w', encoding),
                 'entries': sorted_entries[:10]}
                ]

        for j in jobs:
            template = jinja_env.get_template(j['tname'])
            context['entries'] = j['entries']
            html = template.render(context)
            j['output'].write(html)
            j['output'].close()

        return True


class Entry(object):

    @classmethod
    def entry_from_db(kls, filename):
        f=os.path.join(os.path.join(CONFIG['content_root'], filename))
        return kls(f)

    def __init__(self, path):
        self._path = path
        self.path = path.split(CONFIG['content_root'])[-1]
        self.entry_template = jinja_env.get_template("entry.html")
        self.prepare()

    def __str__(self):
        return self.path

    def __repr__(self):
        return self.path

    @property
    def name(self):
        return os.path.splitext(os.path.basename(self.path))[0]

    @property
    def abspath(self):
        return self._path

    @property
    def destination(self):
        dest = "%s/%s/index.html" % (KINDS[
                                     self.kind]['name_plural'], self.name)
        print dest
        return os.path.join(CONFIG['output_to'], dest)

    @property
    def title(self):
        return self.header['title']

    @property
    def summary_html(self):
        return "%s" % markdown2.markdown(self.header['summary'].strip())

    @property
    def credits_html(self):
        return "%s" % markdown2.markdown(self.header['credits'].strip())

    @property
    def summary_atom(self):
        summarya = markdown2.markdown(self.header['summary'].strip())
        summarya = re.sub("<p>|</p>", "", summarya)
        more = '<a href="%s"> continue reading...</a>' % (self.permalink)
        return summarya+more

    @property
    def publish_date(self):
        return self.header['published'].strftime("%B %d, %Y")

    @property
    def published_atom(self):
        return self.published.strftime("%Y-%m-%dT%H:%M:%SZ")

    @property
    def atom_id(self):
        return "tag:%s,%s:%s" % \
            (
                self.published.strftime("%Y-%m-%d"),
                self.permalink,
                GLOBAL_TEMPLATE_CONTEXT["site_url"]
            )

    @property
    def body_html(self):
        if renderer == 'md2':
            return markdown2.markdown(self.body, extras=['fenced-code-blocks',
                                                         'hilite',
                                                         'tables'])
        if renderer == 'md1':
            return markdown.markdown(self.body,
                                     extensions=['fenced_code',
                                                 'codehilite(linenums=False)',
                                                 'tables'])

    @property
    def permalink(self):
        return "/%s/%s" % (KINDS[self.kind]['name_plural'], self.name)

    @property
    def tags(self):
        return [Tag(t) for t in self.header['tags']]

    def _read_header(self, file):
        header = ['---']
        while True:
            line = file.readline()
            line = line.rstrip()
            if not line:
                break
            header.append(line)
        header = yaml.load(StringIO('\n'.join(header)))
        # todo: dispatch header to attribute
        # todo: parse date from string to a datetime object
        return header

    def prepare(self):
        file = codecs.open(self.abspath, 'r')
        self.header = self._read_header(file)
        self.date = self.header.get('published', datetime.date.today())
        for k, v in self.header.items():
            try:
                setattr(self, k, v)
            except:
                pass

        body = file.readlines()

        self.body = ''.join(body)
        file.close()


    def render(self):
        if not self.header['public']:
            return False

        try:
            os.makedirs(os.path.dirname(self.destination))
        except OSError:
            pass

        context = GLOBAL_TEMPLATE_CONTEXT.copy()
        context['entry'] = self

        try:
            html = self.entry_template.render(context)
        except Exception as e:  # pragma: no cover
            print context
            print self.path
            print e
            sys.exit()
        destination = codecs.open(
            self.destination, 'w', CONFIG['content_encoding'])
        destination.write(html)
        destination.close()

        return True


def _sort_entries(entries):
    """Sort all entries by date and reverse the list"""
    return list(reversed(sorted(entries, key=operator.attrgetter('date'))))


def render_archive(entries):
    """
    This function creates the archive page

    To function it need to read:

     - entry title
     - entry publish date
     - entry permalink

    Until now, this was parsed from each entry YAML...
    It would be more convinient to read this from the DB.

    This requires changes for the database.
    """
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    context['entries'] = entries[ARCHIVE_SIZE:]
    template = jinja_env.get_template('archive_index.html')
    html = template.render(context)
    try:
        os.makedirs(os.path.join(CONFIG['output_to'], 'archive'))
    except OSError:
        pass

    destination = codecs.open("%s/archive/index.html" % CONFIG[
                              'output_to'], 'w', CONFIG['content_encoding'])
    destination.write(html)
    destination.close()


def find_new_posts(posts_table):
    """
    Walk content dir, put each post in the database
    """
    Posts = Query()
    for root, dirs, files in os.walk(CONFIG['content_root']):
        for filename in files:
            if filename.endswith(('md', 'markdown')):
                fullpath = os.path.join(root, filename)
                if not posts_table.contains(Posts.filename == fullpath):
                    post_id = posts_table.insert({'filename': fullpath})
                    yield post_id, fullpath


def _get_last_entries():
    eids = [post.eid for post in DB.posts.all()]
    eids = sorted(eids)[-10:][::-1]
    entries = [Entry(DB.posts.get(eid=eid)['filename']) for eid in eids]
    return entries


def update_index():
    """find the last 10 entries in the database and create the main
    page.
    Each entry in has an eid, so we only get the last 10 eids.

    This method also updates the ATOM feed.
    """
    entries = _get_last_entries()
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    context['entries'] = entries

    for name, out in {'entry_index.html': 'index.html',
                      'atom.xml': 'atom.xml'}.items():
        template = jinja_env.get_template(name)
        html = template.render(context)
        destination = codecs.open("%s/%s" % (CONFIG['output_to'], out),
                                  'w', CONFIG['content_encoding'])
        destination.write(html)
        destination.close()


def new_build():
    """

        a. For each new post:
        1. render html
        2. find post tags
        3. update atom feeds for old tags
        4. create new atom feeds for new tags

    b. update index page
    c. update archive page

    """
    print
    print "Rendering website now..."
    print
    print " entries:"
    entries = list()
    tags = dict()
    root = CONFIG['content_root']
    for post_id, post in find_new_posts(DB.posts):
        try:
            entry = Entry(post)
            if entry.render():
                entries.append(entry)
                for tag in entry.tags:
                    tag.posts = [post_id]
                    tags[tag.name] = tag
            print "     %s" % entry.path
        except Exception as e:
            print "Found some problem in: ", post
            print e
            print "Please correct this problem ..."
            sys.exit(1)

    for name, to in tags.iteritems():
        print "updating tag %s" % name
        to.render()

    # update index
    print "updating index"
    update_index()

    # update archive
    print "updating archive"
    render_archive(_sort_entries([Entry(p['filename'])
                                  for p in DB.posts.all()]))




class StoppableHTTPServer(BaseHTTPServer.HTTPServer):  # pragma: no coverage

    def server_bind(self):
        BaseHTTPServer.HTTPServer.server_bind(self)
        self.socket.settimeout(1)
        self.run = True

    def get_request(self):
        while self.run:
            try:
                sock, addr = self.socket.accept()
                sock.settimeout(None)
                return (sock, addr)
            except socket.timeout:
                pass

    def stop(self):
        self.run = False

    def serve(self):
        while self.run:
            self.handle_request()


def preview():  # pragma: no coverage
    """launch an HTTP to preview the website"""
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    SocketServer.TCPServer.allow_reuse_address = True
    port = CONFIG['http_port']
    httpd = SocketServer.TCPServer(("", port), Handler)
    os.chdir(CONFIG['output_to'])
    print "and ready to test at http://127.0.0.1:%d" % CONFIG['http_port']
    print "Hit Ctrl+C to exit"
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


def publish(GITDIRECTORY=CONFIG['output_to']):  # pragma: no coverage
    sp.call('git push', cwd=GITDIRECTORY, shell=True)


def new_post(GITDIRECTORY=CONFIG['output_to'],
             kind=KINDS['writing']):  # pragma: no coverage

    """
    This function should create a template for a new post with a title
    read from the user input.
    Most other fields should be defaults.
    """
    title = raw_input("Give the title of the post: ")
    while ':' in title:
        title = raw_input("Give the title of the post (':' not allowed): ")

    author = CONFIG['author']
    date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
    tags = '[' + raw_input("Give the tags, separated by ', ':") + ']'
    published = 'yes'
    chronological = 'yes'
    summary = ("summary: |\n    Type your summary here.\n    Do not change the "
               "indentation"
               "to the left\n    ...\n\nStart writing your post here!")

    # make file name
    fname = os.path.join(os.getcwd(), 'content', kind['name_plural'],
                         datetime.datetime.strftime(datetime.datetime.now(),
                                                    '%Y'),
                         date+'-'+title.replace(' ', '-')+'.markdown')

    with open(fname, 'w') as npost:
        npost.write('title: %s\n' % title)
        npost.write('author: %s\n' % author)
        npost.write('published: %s\n' % date)
        npost.write('tags: %s\n' % tags)
        npost.write('public: %s\n' % published)
        npost.write('chronological: %s\n' % chronological)
        npost.write('kind: %s\n' % kind['name'])
        npost.write('%s' % summary)

    print '%s %s' % (CONFIG['editor'], repr(fname))
    os.system('%s %s' % (CONFIG['editor'], fname))


def clean(GITDIRECTORY=CONFIG['output_to']):  # pragma: no coverage
    directoriestoclean = ["writings", "notes", "links", "tags", "archive"]
    os.chdir(GITDIRECTORY)
    for directory in directoriestoclean:
        shutil.rmtree(directory)


def dist(SOURCEDIR=os.getcwd()+"/content/",
         DESTDIR=CONFIG['raw_content']):  # pragma: no coverage
    """
    sync raw files from SOURCE to DEST
    """
    sp.call(["rsync", "-avP", SOURCEDIR, DESTDIR], shell=False,
            cwd=os.getcwd())


def main():   # pragma: no coverage
    parser = argparse.ArgumentParser(
        description='blogit - a tool to blog on github.')
    parser.add_argument('-b', '--build', action="store_true",
                        help='convert the markdown files to HTML')
    parser.add_argument('-p', '--preview', action="store_true",
                        help='Launch HTTP server to preview the website')
    parser.add_argument('-c', '--clean', action="store_true",
                        help='clean output files')
    parser.add_argument('-n', '--new', action="store_true",
                        help='create new post')
    parser.add_argument('-d', '--dist', action="store_true",
                        help='sync raw files from SOURCE to DEST')
    parser.add_argument('--publish', action="store_true",
                        help='push built HTML to git upstream')

    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()
    if args.clean:
        clean()
    if args.build:
        new_build()
    if args.dist:
        dist()
    if args.preview:
        preview()
    if args.new:
        new_post()
    if args.publish:
        publish()

if __name__ == '__main__':  # pragma: no coverage
    main()
