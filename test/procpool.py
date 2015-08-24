from __future__ import print_function
from __future__ import unicode_literals

import sys

# Import the development version of treetaggerwrapper.
sys.path.insert(0, "..")

import sys

def start_test(n=None):
    import treetaggerpoll
    import treetaggerwrapper

    #treetaggerwrapper.enable_debugging_log()
    # Note: print() have been commented, you may uncomment them to see progress.
    p = treetaggerpoll.TaggerProcessPoll(workerscount=n, wantresult=False)
    JOBSCOUNT = 10000
    res = []

    text = "This is Mr John's own house, it's very nice." * 40

    print("Creating jobs")
    for i in range(JOBSCOUNT):
        # print("\tJob", i)
        res.append(p.tag_text_async(text))

    print("Waiting for jobs to be completed")
    for i, r in enumerate(res):
        # print("\tJob", i)
        r.wait_finished()
        # print(str(r.result)[:50])
        res[i] = None   # Loose Job reference - free it.

    p.stop_poll()
    print("Finished")

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        nproc = int(sys.argv[1])
    else:
        nproc = None
    start_test(nproc)

