import os

import pytest
from tinydb import Query, where

from blogit.blogit import (CONFIG, find_new_posts_and_pages, DataBase,
                           Entry, Tag, _sort_entries, _get_last_entries,
                           render_archive, update_index, build)

import blogit.blogit as m


CONFIG['content_root'] = 'test_root'
ARCHIVE_SIZE = 10
db_name = os.path.join(CONFIG['content_root'], 'blogit.db')


if os.path.exists(db_name):
    import shutil
    shutil.rmtree(CONFIG['content_root'])

if not os.path.exists(CONFIG['content_root']):
    os.mkdir(CONFIG['content_root'])

DB = DataBase(os.path.join(CONFIG['content_root'], 'blogit.db'))

# monkey patch to local DB
m.DB = DB
Tag.table = DB.tags
Tag.db = DB
Entry.db = DB

tags = ['foo', 'bar', 'baz', 'bug', 'buf']

shift = lambda l, n: l[-n:] + l[:-n]

post = '''\
---
title: Blog post {number}
author: Famous author
published: 2015-01-{number}
tags: {tags}
public: yes
chronological: yes
kind: writing
summary: This is a summry of post {number}. Donec id elit non mi porta gravida at eget metus. Fusce dapibus
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

shift_factors = map(lambda x: (x - 1) / 5 +1,   range(1,21))


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
                           'post{}.md'.format(i))), 'w')
    f.write(post.format(**{'number': i,
                           'tags':
                           ','.join(shift(tags, shift_factors[i-1])[:-1])}))

[write_file(i) for i in range(1, 21)]


def test_find_new_posts_and_pages():
    entries = [e for e in find_new_posts_and_pages(DB)]
    assert len(entries)
    pages = [e[1] for e in entries if str(e[0]).endswith('page.md')]
    assert len(pages)

    assert len(DB.posts.all()) == 20

    entries = [e for e in find_new_posts_and_pages(DB)]
    # no new posts sould be found
    assert len(DB.posts.all()) == 20

    [e[0].tags for e in entries]
    foo = DB.tags.search(where('name')=='foo')
    assert foo[0]['post_ids'] == range(1, 16)

def test_tags():
    entries = map(Entry.entry_from_db,
                  [os.path.join(CONFIG['content_root'], e.get('filename'))
                      for e in DB.posts.all()])
    tags = DB.tags.all()

    t = entries[0].tags

    assert len(t) == 4
    assert t[0].name == u'buf'

    new_tag = Tag('buggg')
    new_tag.posts = [100,100]
    with pytest.raises(ValueError):
        new_tag.posts = "This should not work"
    with pytest.raises(ValueError):
        new_tag.posts = 1  # This should not either


def test_slug():

    t = Tag('foo:bar')
    assert t.slug == "foo-bar"
    t = Tag('foo:;bar,.,baz')
    assert t.slug == "foo-bar-baz"


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


def test_tag_post_ids():
    m ="""\
---
title: Blog post {}
author: Famous author
published: 2015-01-{}
    tags: tag1, tag2
public: yes
chronological: yes
kind: writing
summary: This is a summry
---
"""
    with open(os.path.join(CONFIG['content_root'], 'e.md'), 'w') as f:
        f.write(m.format(25, 25))
    with open(os.path.join(CONFIG['content_root'], 'f.md'), 'w') as f:
        f.write(m.format(27, 27))

    e1 = Entry(os.path.join(CONFIG['content_root'], 'e.md'))
    e1.tags

    e2 = Entry(os.path.join(CONFIG['content_root'], 'f.md'))
    e2.tags

    assert e1.tags[0].posts == e2.tags[0].posts
    e1.render()
    [t.render() for t in e1.tags]

    l = _sort_entries([e2, e1])
    assert l == [e2, e1]


def test_tag_render():

    p = DB.posts.get(eid=1)
    entry = Entry.entry_from_db(
        os.path.join(CONFIG['content_root'], p.get('filename')))

    #entry = Entry(os.path.join(CONFIG['content_root'], 'post1.md'))
    tags = entry.tags

    assert map(str, tags) == ['buf', 'foo', 'bar', 'baz']
    # the entries are wrongly sorted, need to look at that
    assert tags[0].render()
    assert len(list(tags[0].entries))


def test_get_last_entries():

    le = _get_last_entries(DB)
    assert [e.id for e in le] == range(22, 12, -1)


def test_render_archive():

    entries = [Entry.entry_from_db(
        os.path.join(CONFIG['content_root'], e.get('filename'))) for e in
        DB.posts.all()]

    render_archive(_sort_entries(entries, reversed=True)[ARCHIVE_SIZE:])
    # TODO: assertions here


def test_render_archive():
    update_index(_get_last_entries(DB))
    # TODO: assertions here


def test_build():
    build()
