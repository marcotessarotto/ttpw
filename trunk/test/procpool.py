from __future__ import print_function
from __future__ import unicode_literals

import io
import multiprocessing
import sys

# Import the development version of treetaggerwrapper.
sys.path.insert(0, "..")

#ttpw.enable_debugging_log()

def start_test():
    import treetaggerpoll as ttpoll
    p = ttpoll.TaggerPoll()
    JOBSCOUNT = 100
    res = []

    text = "This is Mr John's own house, it's very nice."
    text = io.open("data/notevoltcond.txt", encoding='utf-8').read()

    print("Creating jobs")
    for i in range(JOBSCOUNT):
        print("\tJob", i)
        res.append(p.tag_text_async(text))

    print("Waiting for jobs to be completed")
    for i, r in enumerate(res):
        print("\tJob", i)
        r.wait_finished()
        print(str(r.result)[:50])
        res[i] = None   # Loose Job reference - free it.

    p.stop_poll()
    print("Finished")

if __name__ == '__main__':
    start_test()

