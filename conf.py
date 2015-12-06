"""
Blogit configuration module.
Following projects like sphinx or django this project, chooses
python code as a configuration language instead of choosing the
ini, yaml, or what ever DSL for configuration.
"""

import datetime
import tinydb

db = tinydb.TinyDB('blogit.db')



CONFIG = {
    'content_root': 'content',  # where the markdown files are
    'output_to': 'oz123.github.com',
    'raw_content': 'oz123.github.com/writings_raw/content',
    'templates': 'templates',
    'date_format': '%Y-%m-%d',
    'base_url': 'http://oz123.github.com',
    'http_port': 3030,
    'content_encoding': 'utf-8',
    'author': 'Oz Nahum Tiram',
    'editor': 'editor'
    }


# TODO replace this with a namedtuple for a more convinient access and safety
DB = {'posts': db.table('posts'), 'tags': db.table('tags'),
      'pages': db.table('pages'), 'templates': db.table('templates') }


# EDIT THIS PARAMETER TO CHANGE ARCHIVE SIZE
# 0 Means that all the entries will be in the archive
# 10 meas that all the entries except the last 10
ARCHIVE_SIZE = 0

GLOBAL_TEMPLATE_CONTEXT = {
    'media_base': '/media/',
    'media_url': '../media/',
    'site_url': 'http://oz123.github.com',
    'last_build': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    'twitter': 'https://twitter.com/#!/OzNTiram',
    'stackoverflow': "http://stackoverflow.com/users/492620/oz123",
    'github': "https://github.com/oz123",
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
