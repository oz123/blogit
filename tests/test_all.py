import os
import sys
import pytest
from bs4 import BeautifulSoup
from tinydb import where

sys.path.insert(0, os.getcwd())
from conf import CONFIG  # noqa

db_name = os.path.join(CONFIG['content_root'], 'blogit.db')

if os.path.exists(db_name):
    import shutil
    shutil.rmtree(CONFIG['content_root'])

if not os.path.exists(CONFIG['content_root']):
    os.mkdir(CONFIG['content_root'])

CONFIG['content_root'] = 'test_root'
ARCHIVE_SIZE = 10

from blogit.blogit import (find_new_posts_and_pages, DataBase,  # noqa
                           Entry, Tag, _get_last_entries,
                           render_archive, update_index, build)

import blogit.blogit as m  # noqa


DB = DataBase(os.path.join(CONFIG['content_root'], 'blogit.db'))

# monkey patch to local DB
m.DB = DB
Tag.table = DB.tags
Tag.db = DB
Entry.db = DB

tags = ['foo', 'bar', 'baz', 'bug', 'buf']


def shift(l, n):
    return l[-n:] + l[:-n]

post = '''\
---
title: Blog post {number}
author: Famous author
published: 2015-01-{number}
tags: {tags}
public: yes
chronological: yes
kind: writing
summary: This is a summray of post {number}. Donec id elit non mi porta gravida at eget metus. Fusce dapibus
---

This is the body of post {number}. Donec id elit non mi porta gravida at eget metus. Fusce dapibus, tellus ac cursus commodo, tortor mauris condimentum nibh, ut fermentum massa justo sit amet risus. Etiam porta sem malesuada magna mollis euismod. Donec sed odio dui.

This is a snippet in bash

```bash
$ for i in `seq 1 10`; do
   echo $i
done

VAR="variable"
echo $VAR
# This is a very long long long long long long long long long long comment
```

This is a snippet in python

```python
def yay(top):
    for i in range(1, top+1):
            yield i

for i in yay:
    print(i)
```
'''

try:
    os.mkdir(CONFIG['content_root'])
except OSError:
    pass


shift_factors = list([(x - 1) // 5 + 1 for x in range(1, 21)])

f = open((os.path.join(CONFIG['content_root'],
                       'page.md')), 'w')


f.write("""\
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
""")
f.close()


def write_file(i):
    f = open((os.path.join(CONFIG['content_root'],
                           'post{0:03d}.md'.format(i))), 'w')
    f.write(post.format(**{'number': i,
                           'tags':
                           ','.join(shift(tags, shift_factors[i - 1])[:-1])}))

[write_file(i) for i in range(1, 21)]


def test_find_new_posts_and_pages():
    entries = [e for e in find_new_posts_and_pages(DB)]
    assert len(entries)
    pages = [e[1] for e in entries if str(e[0]).endswith('page.md')]
    assert len(pages)

    assert len(DB.posts.all()) == 20

    new_entries = [e for e in find_new_posts_and_pages(DB)]

    # no new posts sould be found
    assert len(DB.posts.all()) == 20
    assert len(new_entries) == 0

    [e[0].tags for e in entries]
    foo = DB.tags.search(where('name') == 'foo')
    assert foo[0]['post_ids'] == list(range(1, 16))


def test_tags():
    entries = [
        Entry.entry_from_db(os.path.join(CONFIG['content_root'],
                                         e.get('filename')), e.doc_id)
        for e in DB.posts.all()]
    tags = DB.tags.all()  # noqa

    t = entries[0].tags

    assert len(t) == 4
    assert t[0].name == 'buf'

    new_tag = Tag('buggg')
    new_tag.posts = [100, 100]
    with pytest.raises(ValueError):
        new_tag.posts = "This should not work"
    with pytest.raises(ValueError):
        new_tag.posts = 1  # This should not either

    new_tag.posts = [100]
    with pytest.raises(ValueError):
        list(new_tag.entries)


def test_slug():

    t = Tag('foo:bar')
    assert t.slug == "foo-bar"
    t = Tag('foo:;bar,.,baz')
    assert t.slug == "foo-bar-baz"

"""
def test_tag_posts():

    example = Tag('example')

    example.posts = [1,2,3]
    assert [1,2,3] == example.posts

    Filter = Query()
    t = DB.tags.get(Filter.post_ids == [1, 2, 3])
    assert t['post_ids'] == [1, 2, 3]

    example = Tag('example')
    example.posts = [4,5,6]

    rv = DB.tags.search(where('name') == 'example')
    assert rv[0]['post_ids'] == range(1, 7)


def test_tag_entries():
    t = Tag('breaks')
    t.posts = [10000]
    with pytest.raises(ValueError):
        list(t.entries)

    tf = Tag(u'example')
    entries = list(tf.entries)
    assert len(entries)
"""


def test_tag_post_ids():
    m = """\
---
title: Blog post {}
author: Famous author
published: 2015-01-{}
tags: tag1, tag2
public: yes
chronological: yes
kind: writing
summary: This is a summary
---
"""
    assert len(DB.posts.all()) == 20
    with open(os.path.join(CONFIG['content_root'], 'e.md'), 'w') as f:
        f.write(m.format(25, 25))
    with open(os.path.join(CONFIG['content_root'], 'f.md'), 'w') as f:
        f.write(m.format(27, 27))

    e1 = Entry(os.path.join(CONFIG['content_root'], 'e.md'))
    e1.tags

    e2 = Entry(os.path.join(CONFIG['content_root'], 'f.md'))
    e2.tags
    assert len(DB.posts.all()) == 22
    #assert e1.tags[0].posts == e2.tags[0].posts
    e1.render()
    [t.render() for t in e1.tags]

    assert len(DB.posts.all()) == 22


def test_tag_render():
    p = DB.posts.get(doc_id=1)
    entry = Entry.entry_from_db(
        os.path.join(CONFIG['content_root'], p.get('filename')), 1)

    tags = entry.tags

    assert list(map(str, tags)) == ['buf', 'foo', 'bar', 'baz']
    # the entries are wrongly sorted, need to look at that
    assert tags[0].render()
    assert len(list(tags[0].entries))

    assert len(DB.posts.all()) == 22


def test_get_last_entries():

    assert len(DB.posts.all()) == 22
    le, all = _get_last_entries(DB, 10)
    assert [e.id for e in le] == list(range(22, 12, -1))


def test_render_archive():

    entries = [Entry.entry_from_db(
        os.path.join(CONFIG['content_root'], e.get('filename')), e.doc_id) for e in
        DB.posts.all()]

    render_archive(entries[ARCHIVE_SIZE:])
    # pages should not be in the archive
    with open(os.path.join(CONFIG['output_to'], 'archive', 'index.html')) as html_index:
        soup = BeautifulSoup(html_index.read(), 'html.parser')
        assert len(soup.find_all(class_='post')) == 12


def test_render_index():
    le, all_entries = _get_last_entries(DB, 10)
    update_index(le)
    with open(os.path.join(CONFIG['output_to'], 'index.html')) as html_index:
        soup = BeautifulSoup(html_index.read(), 'html.parser')
        assert len(soup.find_all(class_='clearfix entry')) == 10


def test_build():
    DB._db.purge_tables()
    build(CONFIG)
    # check that the index really contains the last 10 entries
    with open(os.path.join(CONFIG['output_to'], 'index.html')) as html_index:
        soup = BeautifulSoup(html_index.read(), 'html.parser')
        assert len(soup.find_all(class_='clearfix entry')) == 10

    # pages should not be in the archive
    with open(os.path.join(CONFIG['output_to'], 'archive', 'index.html')) as html_index:
        soup = BeautifulSoup(html_index.read(), 'html.parser')
        assert len(soup.find_all(class_='post')) == 12

    with open(os.path.join(CONFIG['output_to'], 'tags', 'foo', 'index.html')) as tag_foo:
        soup = BeautifulSoup(tag_foo.read(), 'html.parser')
        titles = [c.a.string for c in
                  soup.find_all(class_="clearfix entry")]
        for title, idx in zip(titles, list(range(15, 0, -1))):
            assert title.split()[-1] == str(idx)
