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
# Copyright (C) 2013-2016 Oz Nahum Tiram <nahumoz@gmail.com>
# ============================================================================

from __future__ import print_function
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

from jinja2 import Environment, FileSystemLoader
import markdown2
import tinydb
from tinydb import Query, where

sys.path.insert(0, os.getcwd())
from conf import CONFIG, ARCHIVE_SIZE, GLOBAL_TEMPLATE_CONTEXT, KINDS

jinja_env = Environment(lstrip_blocks=True, trim_blocks=True,
                        loader=FileSystemLoader(CONFIG['templates']))


class DataBase(object): # pragma: no cover
    """A thin wrapper around TinyDB instance"""

    def __init__(self, path):
        _db = tinydb.TinyDB(path)
        self.posts = _db.table('posts')
        self.tags = _db.table('tags')
        self.pages = _db.table('pages')
        self.templates = _db.table('templates')
        self._db = _db


DB = DataBase(os.path.join(CONFIG['content_root'], 'blogit.db'))


class Tag(object):

    table = DB.tags
    db = DB

    def __init__(self, name):
        self .name = name
        self.permalink = GLOBAL_TEMPLATE_CONTEXT["site_url"]

        Tags = Query()
        tag = self.table.get(Tags.name == self.name)
        if not tag:
            self.table.insert({'name': self.name, 'post_ids': []})

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    @property
    def slug(self):
        _slug = self.name.lower()
        _slug = re.sub(r'[;:,. ]+', '-', _slug)
        return _slug

    @property
    def posts(self):
        """
        return a list of post ids tagged with Tag
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

        # if not tag:  # pragma: no coverage
        #     raise ValueError("Tag %s not found" % self.name)
        # else:
        new = set(post_ids) - set(tag['post_ids'])

        tag['post_ids'].extend(list(new))
        self.table.update({'post_ids': tag['post_ids']}, eids=[tag.eid])

    @property
    def entries(self):
        """return the actual lists of entries tagged with"""
        Posts = Query()
        for id in self.posts:
            post = self.db.posts.get(eid=id)
            if not post:
                 raise ValueError("no post found for eid %s" % id)
            yield Entry(os.path.join(CONFIG['content_root'], post['filename']))

    def render(self):
        """Render html page and atom feed"""
        context = GLOBAL_TEMPLATE_CONTEXT.copy()
        context['tag'] = self
        context['entries'] = _sort_entries(self.entries)

        # render html page
        render_to = os.path.join(CONFIG['output_to'], 'tags', self.slug)
        if not os.path.exists(render_to):
            os.makedirs(render_to)
        _render(context, 'tag_index.html', os.path.join(render_to, 'index.html'))
        # render atom.xml
        context['entries'] = context['entries'][:10]
        _render(context, 'atom.xml', os.path.join(render_to, 'atom.xml'))
        return True


class Entry(object):

    """This is the base class for creating an HTML page from a Markdown
    based page.

    The file has the following structure for a page:

    .. code:

        ---
        title: example page
        public: yes
        kind: page
        template: about.html
        ---
        # some heading

        content paragraph

        ## heading 2

        some more content

    The file has the following structure for a blog entry:

    .. code:

        ---
        title: Blog post 1
        author: Famous author
        published: 2015-01-11
        tags: [python, git, bash, linux]
        public: yes
        chronological: yes
        kind: writing
        summary: This is a summry of post 1. Donec id elit non mi porta
        ---

        This is the body of post 1. Donec id elit non mi porta gravida
    """

    db = DB

    @classmethod
    def entry_from_db(kls, filename):
        f = os.path.join(filename)
        return kls(f)

    def __init__(self, path):
        self._path = path
        self.path = path.split(CONFIG['content_root'])[-1].lstrip('/')
        self.id = None  # this is set inside prepare()
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
        return os.path.join(CONFIG['output_to'], self.permalink)

    @property
    def title(self):
        return self.header['title']

    @property
    def summary_html(self):
        return "%s" % markdown2.markdown(self.header.get('summary', "").strip())

    @property
    def summary_atom(self):
        summarya = markdown2.markdown(self.header.get('summary', "").strip())
        summarya = re.sub("<p>|</p>", "", summarya)
        more = '<a href="%s"> continue reading...</a>' % (self.permalink)
        return summarya+more

    @property
    def publish_date(self):
        return self.header.get('published',
                               datetime.date.today().strftime("%Y-%m-%d"))

    @property
    def permalink(self):
        if self.kind == 'page':
            dest = '%s.html' % self.title.replace('/', "-")
        else:
            dest = "%s/%s/index.html" % (KINDS[self.kind]['name_plural'], self.name)
            dest = dest.lstrip('/')

        return dest

    @property
    def tags(self):
        """this property is always called after prepare"""
        if 'tags' in self.header:
            tags = [Tag(t) for t in self.header['tags']]
            map(lambda t: setattr(t, 'posts', [self.id]), tags)
            return tags
        else:
            return []

    def prepare(self):

        self.body_html = markdown2.markdown(
                codecs.open(self.abspath, 'r').read(),
                extras=['fenced-code-blocks', 'hilite', 'tables', 'metadata'])

        self.header = self.body_html.metadata

        if 'tags' in self.header:  # pages can lack tags
            self.header['tags'] = self.header['tags'].split(',')

        self.date = self.header.get('published', datetime.date.today())

        if isinstance(self.date, unicode):
            self.date = datetime.datetime.strptime(self.date, "%Y-%m-%d")
        for k, v in self.header.items():
            try:
                setattr(self, k, v)
            except AttributeError:
                pass

        if self.header['kind'] == 'writing':
            rv = Entry.db.posts.search(where('filename') == self.path)
            if not rv:
                _id = Entry.db.posts.insert({'filename': self.path})
            else:
                _id = rv[0].eid

        elif self.header['kind'] == 'page':
            rv = Entry.db.pages.search(where('filename') == self.path)
            if not rv:
                _id = Entry.db.pages.insert({'filename': self.path})
            else:
                _id = rv[0].eid

        self.id = _id

    def render(self):
        if not self.header['public']:
            return False

        try:
            context = GLOBAL_TEMPLATE_CONTEXT.copy()
            context['entry'] = self
            _render(context, self.header.get('template', 'entry.html'),
                    self.destination)
            return True
        except Exception as e:  # pragma: no cover
            print(context)
            print(self.path)
            print(e)
            sys.exit(1)



def _sort_entries(entries):
    """Sort all entries by date and reverse the list"""
    return list(reversed(sorted(entries, key=operator.attrgetter('date'))))


def _render(context, template_path, output_path, encoding='utf-8'):
    template = jinja_env.get_template(template_path)
    rendered = template.render(context)
    html = template.render(context)
    try:
        os.makedirs(os.path.dirname(output_path))
    except OSError:
        pass
    destination = codecs.open(output_path, 'w', encoding)
    destination.write(html)
    destination.close()


def render_archive(entries):
    """
    This function creates the archive page
    """
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    context['entries'] = entries[ARCHIVE_SIZE:10]

    _render(context, 'archive_index.html',
            os.path.join(CONFIG['output_to'],'archive/index.html')),


def find_new_posts_and_pages(db):
    """Walk content dir, put each post and page in the database"""

    Q = Query()
    for root, dirs, files in os.walk(CONFIG['content_root']):
        for filename in files:
            if filename.endswith(('md', 'markdown')):
                fullpath = os.path.join(root, filename)
                if not db.posts.contains(Q.filename == fullpath) and \
                        not db.pages.contains(Q.filename == fullpath):
                    e = Entry(fullpath)
                    yield e, e.id


def _get_last_entries():
    eids = [post.eid for post in db.posts.all()]
    eids = sorted(eids)[-10:][::-1]
    entries = [Entry(db.posts.get(eid=eid)['filename']) for eid in eids]
    return entries


def update_index(entries):
    """find the last 10 entries in the database and create the main
    page.
    Each entry in has an eid, so we only get the last 10 eids.

    This method also updates the ATOM feed.
    """
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    context['entries'] = entries

    map(lambda x: _render(
        context, x[0], os.path.join(CONFIG['output_to'], x[1])),
        (('entry_index.html', 'index.html'), ('atom.xml', 'atom.xml')))


def build():
    """Incremental build of the website"""

    print("\nRendering website now...\n")
    print("entries:")
    tags = dict()
    root = CONFIG['content_root']
    for post_id, post in find_new_posts_and_pages(DB):
        # entry = post
        # this method will also parse the post's tags and
        # update the db collection containing the tags.
        if post.render():
            if post.header['kind'] in ['writing', 'link']:
                for tag in post.tags:
                    tag.posts = [post_id]
                    tags[tag.name] = tag
        print("%s" % post.path)

    for name, to in tags.iteritems():
        print("updating tag %s" % name)
        to.render()

    # update index
    print("updating index")
    update_index(_get_last_entries())

    # update archive
    print("updating archive")
    render_archive(_sort_entries([Entry(p['filename'])
                                  for p in db.posts.all()]))



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
    print("and ready to test at http://127.0.0.1:%d" % CONFIG['http_port'])
    print("Hit Ctrl+C to exit")
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
    TODO: update this function
    """
    title = raw_input("Give the title of the post: ")
    while ':' in title:
        title = raw_input("Give the title of the post (':' not allowed): ")

    author = CONFIG['author']
    date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
    tags = raw_input("Give the tags, separated by ', ':")
    published = 'yes'
    chronological = 'yes'
    summary = ("summary: Type your summary here.")

    # make file name
    fname = os.path.join(os.getcwd(), 'content', kind['name_plural'],
                         datetime.datetime.strftime(datetime.datetime.now(),
                                                    '%Y'),
                         date+'-'+title.replace(' ', '-')+'.markdown')

    with open(fname, 'w') as npost:
        npost.write('---\n')
        npost.write('title: %s\n' % title)
        npost.write('author: %s\n' % author)
        npost.write('published: %s\n' % date)
        npost.write('tags: %s\n' % tags)
        npost.write('public: %s\n' % published)
        npost.write('chronological: %s\n' % chronological)
        npost.write('kind: %s\n' % kind['name'])
        npost.write('%s' % summary)
        npost.write('---\n')

    print('%s %s' % (CONFIG['editor'], repr(fname)))
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
        build()
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
