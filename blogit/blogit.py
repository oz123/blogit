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
import os
import re
import datetime
import argparse
import logging
import sys
import operator
from pkg_resources import (Requirement, resource_filename, get_distribution,
                           DistributionNotFound)
from distutils.dir_util import copy_tree
from collections import namedtuple
import codecs
import http.server
import subprocess as sp
import socketserver


from jinja2 import Environment, FileSystemLoader, Markup
import markdown2 as md2
import tinydb
from tinydb import Query

try:
    __version__ = get_distribution('blogit').version
except DistributionNotFound:  # pragma: no cover
    __version__ = '0.3'


class Markdown(md2.Markdown):
    _metadata_pat = re.compile("^---\W(?P<metadata>[\S+:\S+\s]+\n)---\n")
    _key_val_pat = re.compile("^\w+:(?! >)\s*(?:[ \t].*\n?)+", re.MULTILINE)
    # this allows key: >
    #                   value
    #                   conutiues over multiple lines
    _key_val_block_pat = re.compile(
        "(\w+:\s+>\n\s+[\S\s]+?)(?=\n\w+\s*:\s*\w+\n|\Z)")

    def _extract_metadata(self, text):
        # fast test
        if not text.startswith("---"):
            return text
        match = self._metadata_pat.match(text)
        if not match:
            return text
        tail = text[len(match.group(0)):]
        metadata_str = match.groupdict()['metadata']

        kv = re.findall(self._key_val_pat, metadata_str)
        kvm = re.findall(self._key_val_block_pat, metadata_str)
        kvm = [item.replace(": >\n", ":", 1) for item in kvm]

        for item in kv + kvm:
            k, v = item.split(":", 1)
            self.metadata[k.strip()] = v.strip()

        return tail


def markdown(text, html4tags=False, tab_width=4,
             safe_mode=None, extras=None, link_patterns=None,
             use_file_vars=False):
    return Markdown(html4tags=html4tags, tab_width=tab_width,
                    safe_mode=safe_mode, extras=extras,
                    link_patterns=link_patterns,
                    use_file_vars=use_file_vars).convert(text)


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

sys.path.insert(0, os.getcwd())


# before quickstart was run, there is no conf...
try:
    from conf import CONFIG, GLOBAL_TEMPLATE_CONTEXT
    jinja_env = Environment(lstrip_blocks=True, trim_blocks=True,
                            loader=FileSystemLoader(CONFIG['templates']))

    def s2md(text):
        return Markup(markdown(text,
                               extras=['fenced-code-blocks',
                                       'hilite', 'tables']))

    jinja_env.filters['markdown'] = s2md

    class DataBase(object):  # pragma: no coverage

        """A thin wrapper around TinyDB instance"""

        def __init__(self, path):
            self._db = tinydb.TinyDB(path)
            self.posts = self._db.table('posts')
            self.tags = self._db.table('tags')
            self.pages = self._db.table('pages')
            self.templates = self._db.table('templates')

        def __getitem__(self, key):
            return self._db.table(key)

    # this won't work when installing - content root does not exist
    DB = DataBase(os.path.join(CONFIG['content_root'], 'blogit.db'))
except (ImportError, OSError):  # pragma: no coverage
    cwd = os.getcwd()
    CONFIG = {'output_to': cwd, 'content_root': os.path.join(cwd, 'content')}
    DataBaseDummy = namedtuple('DataBaseDummy', ['path', 'tags'])
    DB = DataBaseDummy('dummy', 'tags')

# with this config, pages are rendered to the location of their title
KINDS = {'writing': {'name': 'writing', 'name_plural': 'writings', }, }


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

    def __repr__(self):  # pragma: no coverage
        return self.name

    @property
    def slug(self):
        _slug = self.name.lower()
        _slug = re.sub(r'[;:,. ]+', '-', _slug.lstrip(',.;:-'))
        return _slug.lstrip('-')

    def set_posts(self, post_ids):
        if not isinstance(post_ids, list):
            raise ValueError("post_ids must be of type list")
        Tags = Query()
        tag = self.table.get(Tags.name == self.name)

        new = set(post_ids) - set(tag['post_ids'])

        tag['post_ids'].extend(list(new))
        self.table.update({'post_ids': tag['post_ids']}, eids=[tag.eid])

    posts = property(fget=None, fset=set_posts)

    @property
    def entries(self):
        """return the actual lists of entries tagged with"""
        Tags = Query()
        tag = self.table.get(Tags.name == self.name)
        posts = tag['post_ids']

        for id in posts:
            post = self.db.posts.get(eid=id)
            if not post:  # pragma: no coverage
                raise ValueError("No post found for eid %s" % id)
            yield Entry(os.path.join(CONFIG['content_root'], post['filename']), id)  # noqa

    def render(self):
        """Render html page and atom feed"""
        context = GLOBAL_TEMPLATE_CONTEXT.copy()
        context['tag'] = self
        entries = list(self.entries)
        entries.sort(key=operator.attrgetter('date'), reverse=True)
        context['entries'] = entries

        # render html page
        render_to = os.path.join(CONFIG['output_to'], 'tags', self.slug)
        if not os.path.exists(render_to):  # pragma: no coverage
            os.makedirs(render_to)
        _render(context, 'tag_index.html', os.path.join(render_to, 'index.html'))  # noqa

        # render atom.xml
        context['entries'] = context['entries'][:10]
        context['last_build'] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa

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
        tags: python, git, bash, linux
        public: yes
        chronological: yes
        kind: writing
        summary: This is a summry of post 1. Donec id elit non mi porta
        ---

        This is the body of post 1. Donec id elit non mi porta gravida
    """

    db = DB

    @classmethod
    def entry_from_db(kls, filename, eid=None):
        f = os.path.join(filename)
        return kls(f, eid)

    def __init__(self, path, eid=None):
        self._path = path
        self.path = path.split(CONFIG['content_root'])[-1].lstrip('/')
        self.id = eid  # this is set inside prepare()
        try:
            self.prepare()
        except KeyError:  # pragma: no coverage
            pass

    def __str__(self):
        return self.path

    def __repr__(self):  # pragma: no coverage
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
    def publish_date(self):
        try:
            r = datetime.datetime.strptime(self.header.get('published', ''),
                                           "%Y-%m-%d")
        except ValueError:  # pragma: no coverage
            r = datetime.date.today()
        return r

    @property
    def permalink(self):
        if self.kind == 'page':
            dest = '%s.html' % self._path.replace('.md', "")
        else:
            dest = "%s/%s/index.html" % (KINDS[self.kind]['name_plural'],
                                         self.name)
            dest = dest.lstrip('/')

        return dest

    @property
    def tags(self):
        """this property is always called after prepare"""
        if 'tags' in self.header:
            tags = [Tag(t) for t in self.header['tags']]
            list(map(lambda t: setattr(t, 'posts', [self.id]), tags))
            return tags
        else:
            return []

    def prepare(self):

        self.body_html = markdown(
            codecs.open(self.abspath, 'r').read(),
            extras=['fenced-code-blocks', 'hilite', 'tables', 'metadata'])

        self.header = self.body_html.metadata
        """a blog post without tags causes an error ..."""
        if 'tags' in self.header:  # pages can lack tags
            self.header['tags'] = [t.strip().lower() for t in
                                   self.header['tags'].split(',')]

        else:
            self.header['tags'] = ("",)

        self.date = self.header.get('published', datetime.datetime.now())

        if isinstance(self.date, str):
            self.date = datetime.datetime.strptime(self.date, "%Y-%m-%d")

        for k, v in self.header.items():
            try:
                setattr(self, k, v)
            except AttributeError:
                pass

        if self.id:
            return

        rec = {'filename': self.path,
               'mtime': int(os.path.getmtime(self.abspath))}

        if self.header['kind'] == 'writing':
            _id = Entry.db.posts.insert(rec)

        elif self.header['kind'] == 'page':
            _id = Entry.db.pages.insert(rec)

        self.id = _id

    def render(self):
        try:
            context = GLOBAL_TEMPLATE_CONTEXT.copy()
            context['entry'] = self
            _render(context, self.header.get('template', 'entry.html'),
                    self.header.get('template', self.destination))
            return True
        except Exception:  # pragma: no cover
            logger.exception("Found some problem with %s", self.path)
            sys.exit(1)


def _render(context, template_path, output_path, encoding='utf-8'):
    template = jinja_env.get_template(template_path)
    html = template.render(context)
    try:
        os.makedirs(os.path.dirname(output_path))
    except OSError:
        pass
    destination = codecs.open(output_path, 'w', encoding)
    destination.write(html)
    destination.close()


def render_archive(entries):
    """Creates the archive page"""
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    context['entries'] = entries
    _render(context, 'archive_index.html',
            os.path.join(CONFIG['output_to'], 'archive/index.html')),


def find_new_posts_and_pages(db):
    """Walk content dir, put each post and page in the database"""

    Q = Query()
    for root, dirs, files in os.walk(CONFIG['content_root']):
        for filename in sorted([f for f in files if
                               f.endswith(('md', 'markdown'))]):
            fullpath = os.path.join(root, filename)
            _p = fullpath.split(CONFIG['content_root'])[-1].lstrip('/')
            new_mtime = int(os.path.getmtime(fullpath))
            e, item = None, None

            for collection in ['posts', 'pages']:
                item = db[collection].get(Q.filename == _p)
                if item:
                    if new_mtime > item['mtime']:
                        db[collection].update({'mtime': new_mtime},
                                              eids=[item.eid])
                        e = Entry(fullpath, eid=item.eid)
                    break

            if not item:
                e = Entry(fullpath)
            if e:
                yield e, e.id


def _get_last_entries(db, qty):
    """get all entries and the last qty entries"""
    eids = [post.eid for post in db.posts.all()]
    eids = sorted(eids, reverse=True)
    # bug: here we shoud only render eids[:qty]
    # but we can't use mtimes for sorting. We'll need to add ptime for the
    # database (publish time)
    entries = [Entry(os.path.join(CONFIG['content_root'],
                     db.posts.get(eid=eid)['filename']), eid) for eid in eids]
    # return _sort_entries(entries)[:qty]
    entries.sort(key=operator.attrgetter('date'), reverse=True)
    return entries[:qty], entries


def update_index(entries):
    """find the last 10 entries in the database and create the main
    page.
    Each entry in has an eid, so we only get the last 10 eids.

    This method also updates the ATOM feed.
    """
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    context['entries'] = entries
    context['last_build'] = datetime.datetime.now().strftime(
        "%Y-%m-%dT%H:%M:%SZ")

    list(map(lambda x: _render(context, x[0],
                               os.path.join(CONFIG['output_to'], x[1])),
             (('entry_index.html', 'index.html'), ('atom.xml', 'atom.xml'))))


def _filter_none_public(entries):
    """by default entries are public, but one can hide them"""
    for e in entries:
        if e.header.get('public', 'yes').lower() in ('true', 'yes'):
            yield e


def build(config):
    """Incremental build of the website"""
    logger.info("\nRendering website now...\n")
    logger.info("entries:")
    tags = dict()
    entries = list()
    for post, post_id in find_new_posts_and_pages(DB):
        # this method will also parse the post's tags and
        # update the db collection containing the tags.
        if post.render():
            if post.header['kind'] in ['writing', 'link']:
                for tag in post.tags:
                    tag.posts = [post_id]
                    tags[tag.name] = tag
                entries.append(post)
            logger.info("%s" % post.path)

    for name, to in tags.items():
        logger.info("updating tag %s" % name)
        to.render()

    # This is expensive, we should insert only the recent entries
    # to the index using BeautifulSoup
    # update index
    logger.info("Updating index")
    last_entries, all_entries = _get_last_entries(DB, config['INDEX_SIZE'])
    last_entries = list(_filter_none_public(last_entries))
    update_index(last_entries)

    # update archive
    logger.info("Updating archive")

    # This is expensive, we should insert only the recent entries
    # to the archive using BeautifulSoup

    entries = [Entry.entry_from_db(
               os.path.join(CONFIG['content_root'],
                            e.get('filename')), e.eid) for e in
               DB.posts.all()]
    all_entries = list(_filter_none_public(all_entries))
    all_entries.sort(key=operator.attrgetter('date'), reverse=True)
    render_archive(all_entries[config['ARCHIVE_SIZE']:])


def preview():  # pragma: no coverage
    """launch an HTTP to preview the website"""
    Handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    port = CONFIG['http_port']
    httpd = socketserver.TCPServer(("", port), Handler)
    os.chdir(CONFIG['output_to'])
    try:
        logger.info("and ready to test at "
                    "http://127.0.0.1:%d" % CONFIG['http_port'])
        logger.info("Hit Ctrl+C to exit")
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()


def quick_start():  # pragma: no coverage
    path = resource_filename(Requirement.parse("blogit"), 'blogit/blogit-mir')
    copy_tree(path, '.')


def publish(GITDIRECTORY=CONFIG['output_to']):  # pragma: no coverage
    sp.call('git push', cwd=GITDIRECTORY, shell=True)


def new_post(GITDIRECTORY=CONFIG['output_to'], kind=KINDS['writing']):  # pragma: no coverage # noqa
    """
    This function should create a template for a new post with a title
    read from the user input.
    Most other fields should be defaults.
    TODO: update this function
    """

    title = input("Give the title of the post: ")
    while ':' in title:
        title = input("Give the title of the post (':' not allowed): ")

    author = CONFIG['author']
    date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
    tags = input("Give the tags, separated by ', ':")
    published = 'yes'
    chronological = 'yes'
    summary = ("summary: Type your summary here.")

    # make file name
    fname = os.path.join(os.getcwd(), 'content', kind['name_plural'],
                         datetime.datetime.strftime(datetime.datetime.now(),
                                                    '%Y'),
                         date + '-' + title.replace(' ', '-') + '.markdown')

    with open(fname, 'w') as npost:
        npost.write('---\n')
        npost.write('title: %s\n' % title)
        npost.write('author: %s\n' % author)
        npost.write('published: %s\n' % date)
        npost.write('tags: %s\n' % tags)
        npost.write('public: %s\n' % published)
        npost.write('chronological: %s\n' % chronological)
        npost.write('kind: %s\n' % kind['name'])
        npost.write('%s\n' % summary)
        npost.write('---\n')

    os.system('%s %s' % (CONFIG['editor'], fname))


def get_parser(formatter_class=argparse.HelpFormatter):  # pragma: no coverage
    parser = argparse.ArgumentParser(
        prog='blogit',
        description='blogit - a simple static site generator.',
        formatter_class=formatter_class)
    parser.add_argument('-b', '--build', action="store_true",
                        help='convert the markdown files to HTML')
    parser.add_argument('-p', '--preview', action="store_true",
                        help='Launch HTTP server to preview the website')
    parser.add_argument('-c', '--clean', action="store_true",
                        help='clean output files')
    parser.add_argument('-n', '--new', action="store_true",
                        help='create new post')
    parser.add_argument('--publish', action="store_true",
                        help='push built HTML to git upstream')
    parser.add_argument('--quick-start', action="store_true")
    parser.add_argument('--version', action="store_true")
    return parser


def main():  # pragma: no coverage

    parser = get_parser()
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit()
    if args.version:
        print("This is blogit {}. Copyright Oz N Tiram "
              "<oz.tiram@gmail.com>".format(__version__))
    if args.build:
        build(CONFIG)
    if args.preview:
        preview()
    if args.new:
        new_post()
    if args.publish:
        publish()
    if args.quick_start:
        quick_start()


if __name__ == '__main__':  # pragma: no coverage
    main()
