import os
from blogit.blogit import CONFIG


CONFIG['content_root'] = 'test_root'

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


def write_file(i):
    f = open((os.path.join(CONFIG['content_root'],
                           'post{}.md'.format(i))), 'w')
    f.write(post.format(**{'number': i,
                           'tags': shift(tags, shift_factors[i-1])[:-1]}))

[write_file(i) for i in range(1, 21)]
