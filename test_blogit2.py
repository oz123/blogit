import os
import shutil
from tinydb import Query
from blogit2 import find_new_posts, DB


post_dummy = """title: Blog post {}
author: Famous author
published: 2015-01-16
tags: [python, git, bash]
public: yes
chronological: yes
kind: writing
summary: |
    This is a summry of post {}
    ...

This is the body of post {}
"""

Posts = Query()
if not DB['posts'].contains(Posts.filename == 'post4.md'):
    DB['posts'].insert({'filename': 'post4.md'})


def create_posts():
    os.mkdir('content')
    os.chdir('content')
    for p in range(1,4):
        with open('post'+str(p)+'.md', 'a') as f:
            f.write(post_dummy.format(p,p,p))
    os.chdir('..')

def clean_posts():
    if os.path.exists('content'):
        shutil.rmtree('content')

def test_find_new_posts():
    clean_posts()
    create_posts()
    new =  list(find_new_posts(DB['posts']))
    assert len(DB['posts'])  == 4
    assert len(new) == 3

os.unlink('blogit.db')
