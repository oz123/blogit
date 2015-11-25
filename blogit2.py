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
The content directory can contain only mardown or txt files, no images
allowed!
"""
import os
import re
import datetime
import argparse
import sys
from distutils import dir_util
import shutil
from StringIO import StringIO
import codecs
import subprocess as sp
import SimpleHTTPServer
import BaseHTTPServer
import socket
import thread
try:
    import yaml  # in debian python-yaml
    from jinja2 import Environment, FileSystemLoader  # in debian python-jinja2
except ImportError, e:
    print e
    print "On Debian based system you can install the dependencies with: "
    print "apt-get install python-yaml python-jinja2"
    sys.exit(1)

try:
    import markdown2
    renderer = 'md2'
except ImportError, e:
    try:
        import markdown
        renderer = 'md1'
    except ImportError, e:
        print e
        print "try: sudo pip install markdown2"
        sys.exit(1)

from tinydb import Query
sys.path.insert(0, os.getcwdu())
from conf import CONFIG, ARCHIVE_SIZE, GLOBAL_TEMPLATE_CONTEXT, KINDS, DB
jinja_env = Environment(loader=FileSystemLoader(CONFIG['templates']))


class Tag(object):
    def __init__(self, name):
        super(Tag, self).__init__()
        self.name = name
        self.prepare()
        self.permalink = GLOBAL_TEMPLATE_CONTEXT["site_url"]

    def prepare(self):
        _slug = self.name.lower()
        _slug = re.sub(r'[;;,. ]', '-', _slug)
        self.slug = _slug


class Entry(object):
    def __init__(self, path):
        super(Entry, self).__init__()
        path = path.split('content/')[-1]
        self.path = path
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
        return os.path.abspath(os.path.join(CONFIG['content_root'], self.path))

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
    def published_html(self):
        if self.kind in ['link', 'note', 'photo']:
            return self.header['published'].strftime("%B %d, %Y %I:%M %p")
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
                                                         "tables"])
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
        tags = list()
        for t in self.header['tags']:
            tags.append(Tag(t))
        return tags

    def _read_header(self, file):
        header = ['---']
        while True:
            line = file.readline()
            line = line.rstrip()
            if not line:
                break
            header.append(line)
        header = yaml.load(StringIO('\n'.join(header)))
        return header

    def prepare(self):
        file = codecs.open(self.abspath, 'r')
        self.header = self._read_header(file)

        for h in self.header.items():
            if h:
                try:
                    setattr(self, h[0], h[1])
                except:
                    pass

        body = list()
        for line in file.readlines():
            body.append(line)

        self.body = ''.join(body)
        file.close()

        if self.kind == 'link':
            from urlparse import urlparse
            self.domain_name = urlparse(self.url).netloc
        elif self.kind == 'photo':
            pass
        elif self.kind == 'note':
            pass
        elif self.kind == 'writing':
            pass

    def render(self):
        if not self.header['public']:
            return False

        try:
            os.makedirs(os.path.dirname(self.destination))
        except:
            pass
        context = GLOBAL_TEMPLATE_CONTEXT.copy()

        context['entry'] = self

        try:
            html = self.entry_template.render(context)
        except Exception as e:
            print context
            print self.path
            print e
            sys.exit()
        destination = codecs.open(
            self.destination, 'w', CONFIG['content_encoding'])
        destination.write(html)
        destination.close()

        # before returning write log to csv
        # file name, date first seen, date rendered
        # self.path , date-first-seen, if rendered datetime.now
        return True


class Link(Entry):
    def __init__(self, path):
        super(Link, self).__init__(path)

    @property
    def permalink(self):
        print "self.url", self.url
        raw_input()
        return self.url


def entry_factory():
    pass


def _sort_entries(entries):
    _entries = dict()
    sorted_entries = list()

    for entry in entries:
        _published = entry.header['published'].isoformat()
        _entries[_published] = entry

    sorted_keys = sorted(_entries.keys())
    sorted_keys.reverse()

    for key in sorted_keys:
        sorted_entries.append(_entries[key])
    return sorted_entries


def render_index(entries):
    """
    this function renders the main page located at index.html
    under oz123.github.com
    """
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    context['entries'] = entries[:10]
    template = jinja_env.get_template('entry_index.html')
    html = template.render(context)
    destination = codecs.open("%s/index.html" % CONFIG[
                              'output_to'], 'w', CONFIG['content_encoding'])
    destination.write(html)
    destination.close()


def render_archive(entries, render_to=None):
    """
    this function creates the archive page
    """
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    context['entries'] = entries[ARCHIVE_SIZE:]
    template = jinja_env.get_template('archive_index.html')
    html = template.render(context)
    if not render_to:
        render_to = "%s/archive/index.html" % CONFIG['output_to']
        dir_util.mkpath("%s/archive" % CONFIG['output_to'])

    destination = codecs.open("%s/archive/index.html" % CONFIG[
                              'output_to'], 'w', CONFIG['content_encoding'])
    destination.write(html)
    destination.close()


def render_atom_feed(entries, render_to=None):
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    context['entries'] = entries[:10]
    template = jinja_env.get_template('atom.xml')
    html = template.render(context)
    if not render_to:
        render_to = "%s/atom.xml" % CONFIG['output_to']
    destination = codecs.open(render_to, 'w', CONFIG['content_encoding'])
    destination.write(html)
    destination.close()


def render_tag_pages(tag_tree):
    """
    tag_tree is a dictionary witht the following structure:
        {'python': {'tag': <__main__.Tag object at 0x7f0e56200ed0>, 
                    'entries': [post1.md, post2.md, post3.md]}, 
         'git': {'tag': <__main__.Tag object at 0x7f0e5623c2d0>, 
                    'entries': [post1.md, post2.md, post3.md]}, 
         'bash': {'tag': <__main__.Tag object at 0x7f0e5623c0d0>, 
                    'entries': [post1.md, post2.md, post3.md]}}
    """
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    for t in tag_tree.items():
        context['tag'] = t[1]['tag']
        context['entries'] = _sort_entries(t[1]['entries'])
        destination = "%s/tags/%s" % (CONFIG['output_to'], context['tag'].slug)
        try:
            os.makedirs(destination)
        except:
            pass
        template = jinja_env.get_template('tag_index.html')
        html = template.render(context)
        file = codecs.open("%s/index.html" %
                           destination, 'w', CONFIG['content_encoding'])
        file.write(html)
        file.close()
        render_atom_feed(context[
                         'entries'], render_to="%s/atom.xml" % destination)


def find_new_posts(posts_table):
    """
    Walk content dir, put each post in the database
    """
    Posts = Query()
    for root, dirs, files in os.walk(CONFIG['content_root']):
        for filename in files:
            if filename.endswith(('md', 'markdown')):
                if not posts_table.contains(Posts.filename == filename):
                    post_id = posts_table.insert({'filename': filename})
                    yield post_id, filename



def get_entry_tags(tags_table, entry_tags, entry_id):
    Tags = Query()
    for t.name in entry_tags:
        tag = tags_table.get(Tags.name == t.name)
        if tag:
            tag['post_ids'].append(entry_id)
            tags_table.update({'post_ids': tag['post_ids']})
            yield tag
        else:
            eid = tags_table.insert({'name': t, 'post_ids': [entry_id]})
            yield tags_table.get(eid=eid)


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
    for post_id, post in find_new_posts(DB['posts']):
        try:
            entry = Entry(os.path.join(root, post))
            if entry.render():
                entries.append(entry)
            for tag in get_entry_tags(DB['tags'], entry.tags, post_id):
                pass

            print "     %s" % entry.path
        except Exception as e:
            print "Found some problem in: ", filename
            print e
            print "Please correct this problem ..."
            sys.exit()

def build():
    print
    print "Rendering website now..."
    print
    print " entries:"
    entries = list()
    tags = dict()
    for root, dirs, files in os.walk(CONFIG['content_root']):
        for filename in files:
            try:
                import pdb; pdb.set_trace()
                if filename.endswith(('md', 'markdown')):
                    entry = Entry(os.path.join(root, filename))
                    if entry.render():
                        entries.append(entry)
                        for tag in entry.tags:
                            if tag.name not in tags:
                                tags[tag.name] = {
                                    'tag': tag,
                                    'entries': list(),
                                }
                            tags[tag.name]['entries'].append(entry)
                    print "     %s" % entry.path
            except Exception as e:
                print "Found some problem in: ", filename
                print e
                print "Please correct this problem ..."
                sys.exit()
    print " :done"
    print
    print " tag pages & their atom feeds:"
    render_tag_pages(tags)
    print " :done"
    print
    print " site wide index"
    entries = _sort_entries(entries)
    render_index(entries)
    print "................done"
    print " archive index"
    render_archive(entries)
    print "................done"
    print " site wide atom feeds"
    render_atom_feed(entries)
    print "...........done"
    print
    print "All done "


class StoppableHTTPServer(BaseHTTPServer.HTTPServer):

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


def preview(PREVIEW_ADDR='127.0.1.1', PREVIEW_PORT=11000):
    """
    launch an HTTP to preview the website
    """
    os.chdir(CONFIG['output_to'])
    print "and ready to test at http://127.0.0.1:%d" % CONFIG['http_port']
    print "Hit Ctrl+C to exit"
    try:
        httpd = StoppableHTTPServer(("127.0.0.1", CONFIG['http_port']),
                                    SimpleHTTPServer.SimpleHTTPRequestHandler)
        thread.start_new_thread(httpd.serve, ())
        sp.call('xdg-open http://127.0.0.1:%d' % CONFIG['http_port'],
                shell=True)
        while True:
            continue

    except KeyboardInterrupt:
        print
        print "Shutting Down... Bye!."
        print
        httpd.stop()


def publish(GITDIRECTORY=CONFIG['output_to']):
    sp.call('git push', cwd=GITDIRECTORY, shell=True)


def new_post(GITDIRECTORY=CONFIG['output_to'],
             kind=KINDS['writing']):
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


def clean(GITDIRECTORY=CONFIG['output_to']):
    directoriestoclean = ["writings", "notes", "links", "tags", "archive"]
    os.chdir(GITDIRECTORY)
    for directory in directoriestoclean:
        shutil.rmtree(directory)


def dist(SOURCEDIR=os.getcwd()+"/content/",
         DESTDIR=CONFIG['raw_content']):
    """
    sync raw files from SOURCE to DEST
    """
    sp.call(["rsync", "-avP", SOURCEDIR, DESTDIR], shell=False,
            cwd=os.getcwd())

if __name__ == '__main__':
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
