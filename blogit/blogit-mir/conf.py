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
    'content_root': 'content',  # where the markdown files are
    'output_to': '.',
    'templates': 'templates',
    'date_format': '%Y-%m-%d',
    'http_port': 3030,
    'content_encoding': 'utf-8',
    'author': 'Oz Nahum Tiram',
    'ARCHIVE_SIZE': 10,
    'INDEX_SIZE': 10, # How many entries shoud be in the INDEX
    }

GLOBAL_TEMPLATE_CONTEXT = {
    'media_base': '/media/',
    'media_url': '../media/',
    'site_url': 'http://localhost',
    'twitter': 'https://twitter.com/#YourTwitter',
    'stackoverflow': "http://stackoverflow.com/users/#YourUser",
    'github': "https://github.com/#YouGitHub",
    'site_name': "Oz's Blog"
}


