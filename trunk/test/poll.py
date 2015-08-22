from __future__ import print_function
from __future__ import unicode_literals

import sys
sys.path.insert(0, ".")
import treetaggerwrapper
p = treetaggerwrapper.TaggerPoll()

res = []
text = "This is Mr John's own house, it's very nice."


print("Creating jobs")
for i in range(10):
    print("\tJob", i)
    res.append(p.tag_text_async(text))

# Wait for the jobs to be completed.
print("Waiting for jobs to be completed")
for r in res:
    print("\tJob", i)
    r.wait_finished()
    print(r.result)

p.stop_poll()
print("Finished")