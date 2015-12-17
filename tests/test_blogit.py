import os
import shutil
from tinydb import Query
from blogit.blogit import find_new_posts, DataBase, Entry, Tag
from blogit.blogit import CONFIG, new_build


post_dummy = """title: Blog post{}
author: Famous author
published: 2015-01-1{}
tags: [python, git, bash, linux]
public: yes
chronological: yes
kind: writing
summary: |
    This is a summry of post {}. Donec id elit non mi porta gravida at eget metus. Fusce dapibus
    ...

This is the body of post {}. Donec id elit non mi porta gravida at eget metus. Fusce dapibus, tellus ac cursus commodo, tortor mauris condimentum nibh, ut fermentum massa justo sit amet risus. Etiam porta sem malesuada magna mollis euismod. Donec sed odio dui.

This is a snippet in bash

```bash
$ for i in `seq 1 10`; do
   echo $i
done

VAR="variable"
echo
```

This is a snippet in python

```python
def yay(top):
        for i in range(1, top+1):
                    yield i

    for i in yay:
        print(i)
```
This the last line of the post.
"""

def insert_single(DB):
    Posts = Query()
    if not DB.posts.contains(Posts.filename == 'post4.md'):
        DB.posts.insert({'filename': 'post4.md'})


def create_posts():
    os.mkdir('content')
    os.chdir('content')
    for p in range(1,4):
        with open('post'+str(p)+'.md', 'a') as f:
            f.write(post_dummy.format(p,p,p,p))
    os.chdir('..')

def clean_posts():
    if os.path.exists('content'):
        shutil.rmtree('content')

def test_find_new_posts():
    clean_posts()
    create_posts()
    DB = DataBase(os.path.join(CONFIG['content_root'], 'blogit.db'))
    DB._db.purge_tables()
    insert_single(DB)
    new =  list(find_new_posts(DB.posts))
    assert len(DB.posts.all()) == 4
    assert len(new) == 3


def test_tags():
    t = Tag('bar')
    t.posts = [1]
    assert t.posts == [1]
    t.posts = [1,3,4,5]
    assert t.posts == [1,3,4,5]


def test_new_build():
    DB = DataBase(os.path.join(CONFIG['content_root'], 'blogit.db'))
    DB._db.purge_tables()
    clean_posts()
    create_posts()
    new_build()

post_dummy = """title: Blog post {}
author: Famous author
published: 2015-01-1{}
tags: [python, git, bash, linux]
public: yes
chronological: yes
kind: writing
summary: |
    This is a summry of post {}. Donec id elit non mi porta gravida at eget metus. Fusce dapibus
    ...

This is the body of post {}. Donec id elit non mi porta gravida at eget metus. Fusce dapibus, tellus ac cursus commodo, tortor mauris condimentum nibh, ut fermentum massa justo sit amet risus. Etiam porta sem malesuada magna mollis euismod. Donec sed odio dui.

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
"""

def create_last_post():
    os.chdir('content')
    with open('post'+str(5)+'.md', 'a') as f:
        f.write(post_dummy.format(5,5,5,5))
    os.chdir('..')

def test_new_build2():
    create_last_post()
    new_build()

try:
    os.unlink('blogit.db')
except OSError:
    pass
