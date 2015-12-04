import os
import shutil
from tinydb import Query
from blogit2 import find_new_posts, DB, Entry, Tag
from blogit2 import CONFIG, new_build
from conf import db


post_dummy = """title: Blog post {}
author: Famous author
published: 2015-01-1{}
tags: [python, git, bash, linux]
public: yes
chronological: yes
kind: writing
summary: |
    This is a summry of post {}
    ...

This is the body of post {}
"""
def insert_single():
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
    db.purge_tables()
    insert_single()
    clean_posts()
    create_posts()
    new =  list(find_new_posts(DB['posts']))
    assert len(DB['posts'].all()) == 4
    assert len(new) == 3


def test_tags():
    t = Tag('bar')
    t.posts = [1]
    assert t.posts == [1]
    t.posts = [1,3,4,5]
    assert t.posts == [1,3,4,5]


def test_new_build():
    db.purge_tables()
    clean_posts()
    create_posts()
    new_build()

post_dummy = """title: Blog post {}
author: Famous author
published: 2015-01-16
tags: [python, git, foo]
public: yes
chronological: yes
kind: writing
summary: |
    This is a summry of post {}
    ...

This is the body of post {}
"""
def create_last_post():
    os.chdir('content')
    with open('post'+str(5)+'.md', 'a') as f:
        f.write(post_dummy.format(5,5,5))
    os.chdir('..')

def test_new_build2():
    create_last_post()
    new_build()
    # bug: creating a new post with existing tags
    # removes older tags ...

os.unlink('blogit.db')
