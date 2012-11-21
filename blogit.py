#!/usr/bin/env python
# -*- coding: utf-8


# Copyleft (C) 2010 Mir Nazim <hello@mirnazim.org>
# 
# Everyone is permitted to copy and distribute verbatim or modified
# copies of this license document, and changing it is allowed as long
# as the name is changed.
# 
# TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION
# 
# 0. You just DO WHATEVER THE FUCK YOU WANT TO. (IT'S SLOPPY CODE ANYWAY)
#
# WARANTIES: 
# 0. Are you kidding me?
# 1. Seriously, Are you fucking kidding me?
# 2. If anything goes wrong, sue the "The Empire".


import os
import re
import datetime
import yaml # in debian python-yaml
from StringIO import StringIO
import codecs
from jinja2 import Environment, FileSystemLoader # in debian python-jinja2
import markdown2
import argparse
import sys
from distutils import dir_util

import pdb
CONFIG = {
    'content_root': 'content', # where the markdown files are
    'output_to': 'oz123.github.com',
    'templates': 'templates',
    'date_format': '%Y-%m-%d',
    'base_url': 'oz123.github.com',
    'http_port': 3030,
    'content_encoding': 'utf-8',
}

GLOBAL_TEMPLATE_CONTEXT = {
    'media_base': '/media/',
    'media_url': '../media/',
    'site_url' : 'oz123.github.com',
    'last_build' : datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    'twitter' : 'https://twitter.com/#!/OzNTiram',
    'stackoverflow': "http://stackoverflow.com/users/492620/oz123",
    'github' : "https://github.com/oz123",
    'side_bar': """
<div id="nav">
  <div><img src="/media/img/me.png"></div>
  <a title="Home" href="/">home</a>
  <a title="About" class="about" href="/about.html">about</a>
  <a title="Archive" class="archive" href="/archive">archive</a>
  <a title="Atom feeds" href="/atom.xml">atom</a>
  <a title="Twitter" href="https://twitter.com/#!/OzNTiram">twitter</a>
  <a title="Stackoverflow" href="http://stackoverflow.com/users/492620/oz123">stackoverflow</a>
  <a title="Github" href="https://github.com/oz123">github</a>
</div>
                """
}

KINDS = {
    'writing': {
        'name': 'writing', 'name_plural': 'writings',
    },
    'note': {
        'name': 'note', 'name_plural': 'notes',
    },
    'link': {
        'name': 'link', 'name_plural': 'links',
    },
    'photo': {
        'name': 'photo', 'name_plural': 'photos',
    },
    'page': {
        'name': 'page', 'name_plural': 'pages',
    },

}

jinja_env = Environment(loader=FileSystemLoader(CONFIG['templates']))

class Tag(object):
    def __init__(self, name):
        super(Tag, self).__init__()
        self.name = name
        self.prepare()
        self.permalink = "oz123.github.com"

    def prepare(self):
        _slug = self.name.lower()
        _slug = re.sub(r'[;;,. ]', '-', _slug)
        self.slug = _slug

class Entry(object):
    def __init__(self, path):
        super(Entry, self).__init__()
        path = path.split('content/')[-1]
        self.path = path
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
        dest = "%s/%s/index.html" % (KINDS[self.kind]['name_plural'], self.name)
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
        summarya=markdown2.markdown(self.header['summary'].strip())
        summarya=re.sub("<p>|</p>","",summarya)
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
        return "tag:oz123.github.com,%s:%s" % \
                (
                    self.published.strftime("%Y-%m-%d"),
                    self.permalink,
                )


    @property
    def body_html(self):
        return markdown2.markdown(self.body, extras=['code-color'])


    @property
    def permalink(self):
        return "/%s/%s" % (KINDS[self.kind]['name_plural'], self.name)
       
    @property
    def tags(self):
        tags = list()
        for t in self.header['tags']:
            tags.append(Tag(t))
        return tags


    def prepare(self):
        file = codecs.open(self.abspath, 'r')
        header = ['---']
        while True:
            line = file.readline()
            line = line.rstrip()
            if not line: break
            header.append(line)
        self.header = yaml.load(StringIO('\n'.join(header)))
        for h in self.header.items():
            if h:
                try:
                    setattr(self, h[0], h[1])
                except:
                    pass


        body = list()
        for line in file.readlines():
            body.append(line)
        self.body = '\n'.join(body)
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
        print "context"
        print context
        
        context['entry'] = self
        print "entry", context['entry']
        
        template = jinja_env.get_template("entry.html")
        print "template" , template
        
        #print dir(template)
        #raw_input()
        html = template.render(context)
        print "in render", self.destination
        destination = codecs.open(self.destination, 'w', CONFIG['content_encoding'])
        destination.write(html)
        destination.close()
        return True

class Link(Entry):
    def __init__(self, path):
        super(Link, self).__init__(path)


    @property
    def permalink(self):
        print  "self.url", self.url
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
    destination = codecs.open("%s/index.html" % CONFIG['output_to'], 'w', CONFIG['content_encoding'])
    destination.write(html)
    destination.close()


def render_archive(entries, render_to=None):
    """
    this function creates the archive page
    """
    context = GLOBAL_TEMPLATE_CONTEXT.copy()
    context['entries'] = entries[10:]
    template = jinja_env.get_template('archive_index.html')
    html = template.render(context)
    if not render_to:
        render_to = "%s/archive/index.html" % CONFIG['output_to']
        dir_util.mkpath("%s/archive" % CONFIG['output_to'])
    
    destination = codecs.open("%s/archive/index.html" % CONFIG['output_to'], 'w', CONFIG['content_encoding'])
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
        file = codecs.open("%s/index.html" % destination, 'w', CONFIG['content_encoding'])
        file.write(html)
        file.close()
        #print "    tags/%s" % (context['tag'].slug, )
        render_atom_feed(context['entries'], render_to="%s/atom.xml" % destination)


def build():
    print
    print "Rendering website now..."
    print
    print " entries:"
    entries = list()
    tags = dict()
    for root, dirs, files in os.walk(CONFIG['content_root']):
        for file in files:
            entry = Entry(os.path.join(root, file))
            if entry.render():
                entries.append(entry)
                for tag in entry.tags:
                    if not tags.has_key(tag.name):
                        tags[tag.name] = {
                            'tag': tag,
                            'entries': list(),
                        }
                    tags[tag.name]['entries'].append(entry)
            print "     %s" % entry.path
    print " :done"
    print
    print " tag pages & their atom feeds:"
    render_tag_pages(tags)
    print " :done"
    print
    print " site wide index"
    entries = _sort_entries(entries)
    #render_index(_sort_entries(entries))
    render_index(entries)
    print "................done"
    print " archive index"
    render_archive(entries)
    print "................done"
    print " site wide atom feeds"
    #render_atom_feed(_sort_entries(entries))
    render_atom_feed(entries)
    print "...........done"
    print
    print "All done "


def preview(PREVIEW_ADDR = '127.0.1.1',PREVIEW_PORT = 11000):
    """
    launch an HTTP to preview the website
    """
    import SimpleHTTPServer
    import SocketServer
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", CONFIG['http_port']), Handler)
    os.chdir(CONFIG['output_to'])
    print "and ready to test at http://127.0.0.1:%d" % CONFIG['http_port']
    print "Hit Ctrl+C to exit"
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print
        print "Shutting Down... Bye!."
        print
        httpd.server_close()

def publish(GITDIRECTORY="oz123.github.com"):
    pass
    

if __name__== '__main__':
    parser = argparse.ArgumentParser(description='blogit - a tool blog on github.')
    parser.add_argument('-b','--build', action="store_true",
    help='convert the markdown files to HTML')
    parser.add_argument('-p','--preview', action="store_true",
    help='Launch HTTP server to preview the website')
    
    
    args = parser.parse_args()

    if len(sys.argv) < 2 :
        parser.print_help()
        sys.exit()
    #import pdb; pdb.set_trace()
    if args.build:
        #pdb.set_trace()
        build()
    if args.preview:
        preview()
    
