# -*- encoding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

import treetaggerwrapper as ttpw
import io

tt = ttpw.TreeTagger(LANG='fr')

with io.open("fileslist.txt", encoding="utf-8") as f:
    flist = f.read().splitlines()

for fname in flist:
    print("Tagging:", fname)
    tt.tag_file(fname)

