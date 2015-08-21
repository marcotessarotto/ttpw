# -*- encoding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals

PROFILING = False

if PROFILING:
    import cProfile
import treetaggerwrapper as ttpw
import io
import sys

tt = ttpw.TreeTagger(LANG='fr')

with io.open("fileslist.txt", encoding="utf-8") as f:
    flist = f.read().splitlines()

for fname in flist:
    print("Tagging:", fname)
    if PROFILING:
        cProfile.run("res = tt.tag_file(fname)")
        break   # Just process one file.
    else:
        res = tt.tag_file(fname)
        # Uncomment to save result and diff data.
        #with io.open(fname+str(sys.version_info.major), "w", encoding='utf-8') as f:
        #    f.writelines(res)
