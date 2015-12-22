import os
import shutil
from tinydb import Query
from blogit.blogit import find_new_items, DB, Entry, Tag
from blogit.blogit import CONFIG, new_build


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
echo ${VAR}
```

This is a snippet in python

```
def yay(top):
    for i in range(1, top+1):
		yield i
```

for i in yay:
    print(i)
```
"""

def create_posts():
    os.mkdir('content')
    os.chdir('content')
    for p in range(1,4):
        with open('post'+str(p)+'.md', 'a') as f:
            f.write(post_dummy.format(p,p,p))
    os.chdir('..')


def test_tag():
    new =  list(find_new_items(DB.posts))
    t = Tag('python')
    t.posts = [1,2,3]
    t.render()


import pytest

def test_raises():
    t = Tag('python')
    with pytest.raises(ValueError):
        t.posts = 1
