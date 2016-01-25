#!/usr/bin/env python3

import os

# find all files with md
# for each file
# read file and find the first empty line
# everything following it is the body
# everything before is metadata
# inside metadata convert tags from list with [] to a simple list
# remove pipe from summary
# remove triple dot
# write the new file to old_file
for root, dirs, files in os.walk('.'):
    for filename in files:
        if filename.endswith(('md', 'markdown')):
            fullpath = os.path.join(root, filename).lstrip('./')
            f = open(fullpath).readlines()
            found_meta = False
            for i, l in enumerate(f):
                if not l.strip():
                    meta_end, content_begin = i - 1, i + 1
                    found_meta = True
                    break
            if found_meta:
                newpath = fullpath.split('.')
                newpath.insert(-1,'-new.')
                newpath = ''.join(newpath)
                new = open(''.join(newpath), 'w')
                new.writelines(['---\n'])
                new.writelines(f[0:3])
                new.writelines(f[3].replace('[', '').replace(']',''))
                new.writelines(f[4:meta_end - 2])
                new.writelines(['summary: ' + f[meta_end - 1].lstrip()])
                new.writelines(['---\n'])
                new.writelines(['\n'])
                new.writelines(f[content_begin:])
                new.close()
                os.rename(fullpath, fullpath.replace('.','-old.'))
                os.rename(newpath, fullpath)
                print("Successfuly converted {}".format(fullpath))
            else:
                print("Something fishy with {}".format(new.name))
