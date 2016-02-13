"""
Blogit configuration module.
Following projects like sphinx or django this project, chooses
python code as a configuration language instead of choosing the
ini, yaml, or what ever DSL for configuration.
"""

# ARCHIVE SIZE
# 0 Means that all the entries will be in the archive
# 10 meas that all the entries except the last 10

CONFIG = {
    'content_root': 'test_root',  # where the markdown files are
    'output_to': 'oz123.github.com',
    'raw_content': 'oz123.github.com/writings_raw/content',
    'templates': 'templates',
    'date_format': '%Y-%m-%d',
    'base_url': 'http://oz123.github.com',
    'http_port': 3030,
    'content_encoding': 'utf-8',
    'author': 'Oz Nahum Tiram',
    'editor': 'editor',
    'ARCHIVE_SIZE': 10
    }

GLOBAL_TEMPLATE_CONTEXT = {
    'media_base': '/media/',
    'media_url': '../media/',
    'site_url': 'http://oz123.github.com',
    'twitter': 'https://twitter.com/#!/OzNTiram',
    'stackoverflow': "http://stackoverflow.com/users/492620/oz123",
    'github': "https://github.com/oz123",
}


