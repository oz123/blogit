import os
import shutil
from tinydb import Query
from blogit.blogit import find_new_posts, DB, Entry, Tag
from blogit.blogit import CONFIG, new_build


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

def create_posts():
    os.mkdir('content')
    os.chdir('content')
    for p in range(1,4):
        with open('post'+str(p)+'.md', 'a') as f:
            f.write(post_dummy.format(p,p,p))
    os.chdir('..')


def test_tag():
    new =  list(find_new_posts(DB.posts))
    t = Tag('python')
    t.posts = [1,2,3]
    t.render()

import pytest

def test_raises():
    t = Tag('python')
    with pytest.raises(ValueError):
        t.posts = 1
