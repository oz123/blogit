import os

import pytest
from tinydb import Query

from blogit.blogit import CONFIG, find_new_posts_and_pages, DataBase
from blogit.blogit import Entry, Tag
import blogit.blogit as m


CONFIG['content_root'] = 'test_root'
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
                           'tags': ','.join(shift(tags, shift_factors[i-1])[:-1])}))

[write_file(i) for i in range(1, 21)]


def test_find_new_posts_and_pages():
    entries = [e for e in find_new_posts_and_pages(DB)]
    assert len(entries)
    pages = [e[1] for e in entries if str(e[0]).endswith('page.md')]
    assert len(pages)

    assert len(DB.posts.all()) == 20


def test_tags():
    entries = map(Entry.entry_from_db, [os.path.join(CONFIG['content_root'], e.get('filename')) for e in
                  DB.posts.all()])
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


def test_tag_entries():
    t = Tag('breaks')
    t.posts = [10000]
    with pytest.raises(ValueError):
        list(t.entries)

    tf = Tag(u'example')
    entries = list(tf.entries)
    assert len(entries)

def test_tag_render():

    p = DB.posts.get(eid=1)
    entry = Entry.entry_from_db(os.path.join(CONFIG['content_root'], p.get('filename')))
    tags = entry.tags
    assert map(str, tags) == ['buf', 'foo', 'bar', 'baz']
    assert tags[0].render()
    assert len(list(tags[0].entries))

