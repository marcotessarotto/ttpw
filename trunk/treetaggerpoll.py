#!/bin/env python
# -*- coding: utf-8 -*-

import logging
import threading
import multiprocessing as mp
import treetaggerwrapper as ttpw

# We don't print for errors/warnings, we use Python logging system.
logger = logging.getLogger("TreeTagger.Poll")
# Avoid No handlers could be found for logger "TreeTagger" message.
logger.addHandler(logging.NullHandler())


DEBUG_MULTITHREAD = True

__all__ = []


# ==============================================================================
class TaggerPoll(object):
    """Keep a poll of TreeTaggers process for processing with different threads.

    This class is here for people preferring natural language processing
    over multiprocessing programming… :-)

    Each poll manage a set of threads, able to do parallel chunking, and a
    set of taggers, able to do (more real) parallel tagging.
    All taggers in the same poll are created for same processing (with
    same options).

    :class:`TaggerPoll` objects has same high level interface than :class:`TreeTagger`
    ones with ``_async`` at end of methods names.
    Each of …_asynch method returns a :class:`Job` object allowing to know if
    processing is finished, to wait for it, and to get the result.

    If you want to **properly terminate** a :class:`TaggerPoll`, you must
    call its :func:`TaggerPoll.stop_poll` method.

    .. note::

        Parallel processing via threads in Python within the same
        process is limited due to the global interpreter lock
        (Python's GIL).
        See multiprocessing for real parallel process
        (I may sometime transform TaggerPool to a multiprocessing
        tool — as chunking took a large part of processing and it is
        done in Python, so under the GIL, overall performance gain
        with threading is not excellent).

    **Example of use**

    In this example no parameter is given to the poll, it auto-adapt
    to the count of CPU cores.

    .. code:: python

        import treetaggerwrapper as ttpw
        p = ttpw.TaggerPoll()

        res = []
        text = "This is Mr John's own house, it's very nice."
        print("Creating jobs")
        for i in range(10):
            print("\tJob", i)
            res.append(p.tag_text_async(text))
        print("Waiting for jobs to be completed")
        for i, r in enumerate(res):
            print("\tJob", i)
            r.wait_finished()
            print(r.result)
        p.stop_poll()
        print("Finished")
    """
    def __init__(self, workerscount=None, **kwargs):
        """Creation of a new TaggerPoll.

        By default a :class:`TaggerPoll` creates same count of threads and
        of TreeTagger objects than there are CPU cores on your computer.

        :param workerscount: number of worker threads to create.
        :type workerscount: int
        :param kwargs: same parameters as :func:`TreeTagger.__init__`.
        """
        if workerscount is None:
            workerscount = mp.cpu_count()
        # Security, we need at least one worker and one tagger.
        if workerscount < 1:
            raise ValueError("Invalid workerscount %s", workerscount)

        if DEBUG_MULTITHREAD:
            logger.debug("Creating TaggerPoll, %d workers", workerscount )

        self._stopping = False
        self._workers = []
        self._waitjobs = mp.Queue()
        self._finishedjobs = mp.Queue()
        self._jobsrefs = {}
        self._jobslock = threading.Lock()
        # Following thread retrieve results, store them in corresponding Job, and
        # signal them.
        self._jobsmonitor = threading.Thread(target=self._monitor_main)
        self._jobsmonitor.daemon = True
        self._jobsmonitor.start()

        self._build_workers(workerscount, kwargs)

        if DEBUG_MULTITHREAD:
            logger.debug("TaggerPoll ready")

    def _build_workers(self, workerscount, taggerargs):
        if DEBUG_MULTITHREAD:
            logger.debug("Creating workers for TaggerPoll")
        for i in range(workerscount):
            p = mp.Process(target=self._worker_main,
                            args=(self._waitjobs, self._finishedjobs, taggerargs))
            #th.daemon = True
            self._workers.append(p)
            p.start()

    def _create_job(self, methname, **kwargs):
        if self._stopping:
            raise TreeTaggerError("TaggerPoll is stopped working.")
        job = Job(self, methname, kwargs)
        if DEBUG_MULTITHREAD:
            logger.debug("Job %d created, queuing it", id(job))
        with self._jobslock:
            self._jobsrefs[id(job)] = job
        # We put just pickleable data inside a tuple.
        self._waitjobs.put((id(job), methname, kwargs))
        return job

    def _worker_main(self, requestsqueue, resultsqueue, taggerargs):
        """Main function of a worker thread.

        :param requestsqueue: incoming requests queue of works to do.
        :type requestsqueue: Queue
        :param resultsqueue: outgoing result queue of works done.
        :type resultsqueue: Queue
        :param taggerargs: named parameters dict for creating the
            tagger.
        !type taggerargs: dict
        """
        tagger = ttpw.TreeTagger(**taggerargs)
        while True:
            if DEBUG_MULTITHREAD:
                logger.debug("Worker waiting for work to pick…")
            work = requestsqueue.get()  # Pickup a job.
            if work is None:
                if DEBUG_MULTITHREAD:
                    logger.debug("Worker finishing")
                break   # Put Nones in jobs queue to stop workers.
            # Do the work
            workid, workmeth, workargs = work
            if DEBUG_MULTITHREAD:
                logger.debug("Worker doing picked work %d", workid)
            try:
                meth = getattr(tagger, workmeth)
                result = meth(**workargs)
            except Exception as e:
                if DEBUG_MULTITHREAD:
                    logger.debug("Work %d exit with exception", workid)
                result = e
            # Send back result.
            resultsqueue.put((workid, result))
        del tagger  # Explicitely remove

    def _monitor_main(self):
        while True:
            workresult = self._finishedjobs.get()
            if workresult is None:
                break
            workid, result = workresult
            with self._jobslock:
                job = self._jobsrefs.pop(workid)
            job._set_result(result)

    def stop_poll(self):
        """Properly stop a :class:`TaggerPoll`.

        Takes care of finishing waiting threads, and deleting TreeTagger
        objects (removing pipes connexions to treetagger process).

        Once called, the :class:`TaggerPoll` is no longer usable.
        """
        if DEBUG_MULTITHREAD:
            logger.debug("TaggerPoll stopping")
        if not self._stopping:          # Just stop one time.
            if DEBUG_MULTITHREAD:
                logger.debug("Signaling to threads")
            self._stopping = True       # Prevent more Jobs to be queued.
            # Put one None by process (will awake processes).
            stopmonitor = True
            for x in range(len(self._workers)):
                self._waitjobs.put(None)
        else:
            stopmonitor = True
        # Wait for processed to be finished.
        for p in self._workers:
            if DEBUG_MULTITHREAD:
                logger.debug("Signaling to process %s (pid %d)", p.name, p.pid)
            p.join()
        # Put None for monitoring thread to be finished.
        if stopmonitor:
            self._finishedjobs.put(None)
            self._jobsmonitor.join()

        # Remove refs to process/threads.
        if hasattr(self, '_workers'):
            del self._workers
        if hasattr(self, '_jobsmonitor'):
            del self._jobsmonitor
        if DEBUG_MULTITHREAD:
            logger.debug("TaggerPoll stopped")

    #---------------------------------------------------------------------------
    # Below methods have same interface than TreeTagger to tag texts.
    # --------------------------------------------------------------------------
    def tag_text_async(self, text, numlines=False, tagonly=False,
                 prepronly=False, tagblanks=False, notagurl=False,
                 notagemail=False, notagip=False, notagdns=False,
                 nosgmlsplit=False):
        """
        See :func:`TreeTagger.tag_text` method and :class:`TaggerPoll` doc.

        :return: a :class:`Job` object about the async process.
        :rtype: :class:`Job`
        """
        return self._create_job('tag_text', text=text, numlines=numlines,
                                tagonly=tagonly, prepronly=prepronly,
                                tagblanks=tagblanks, notagurl=notagurl,
                                notagemail=notagemail, notagip=notagip,
                                notagdns=notagdns, nosgmlsplit=nosgmlsplit)

    # --------------------------------------------------------------------------
    def tag_file_async(self, infilepath, encoding=ttpw.USER_ENCODING,
                 numlines=False, tagonly=False,
                 prepronly=False, tagblanks=False, notagurl=False,
                 notagemail=False, notagip=False, notagdns=False,
                 nosgmlsplit=False):
        """
        See :func:`TreeTagger.tag_file` method and :class:`TaggerPoll` doc.

        :return: a :class:`Job` object about the async process.
        :rtype: :class:`Job`
        """
        return self._create_job('tag_file', infilepath=infilepath,
                                encoding=encoding, numlines=numlines,
                                tagonly=tagonly, prepronly=prepronly,
                                tagblanks=tagblanks, notagurl=notagurl,
                                notagemail=notagemail, notagip=notagip,
                                notagdns=notagdns, nosgmlsplit=nosgmlsplit)

    # --------------------------------------------------------------------------
    def tag_file_to_async(self, infilepath, outfilepath, encoding=ttpw.USER_ENCODING,
                    numlines=False, tagonly=False,
                    prepronly=False, tagblanks=False, notagurl=False,
                    notagemail=False, notagip=False, notagdns=False,
                    nosgmlsplit=False):
        """
        See :func:`TreeTagger.tag_file_to` method and :class:`TaggerPoll` doc.

        :return: a :class:`Job` object about the async process.
        :rtype: :class:`Job`
        """
        return self._create_job('tag_file_to', infilepath=infilepath,
                                outfilepath=outfilepath,
                                encoding=encoding, numlines=numlines,
                                tagonly=tagonly, prepronly=prepronly,
                                tagblanks=tagblanks, notagurl=notagurl,
                                notagemail=notagemail, notagip=notagip,
                                notagdns=notagdns, nosgmlsplit=nosgmlsplit)

class Job(object):
    """Asynchronous job to process a text with a Tagger.

    These objects are automatically created for you and returned by
    :class:`TaggerPoll` methods :func:`TaggerPoll.tag_text_async`,
    :func:`TaggerPoll.tag_file_async` and :func:`TaggerPoll.tag_file_to_async`.

    You use them to know status of the asynchronous request, eventually
    wait for it to be finished, and get the final result.

    :ivar finished: Boolean indicator of job termination.
    :ivar result: Final job processing result — or exception.
    """
    def __init__(self, poll, methname, kwargs):
        self._poll = poll
        self._methname = methname
        self._kwargs = kwargs
        self._event = threading.Event()
        self._finished = False
        self._result = None

    def _set_result(self, result):
        self._result = result
        self._finished = True
        self._event.set()
        if DEBUG_MULTITHREAD:
            logger.debug("Job %d finished", id(self))

    @property
    def finished(self):
        return self._finished

    def wait_finished(self):
        """Lock on the Job event signaling its termination.
        """
        self._event.wait()

    @property
    def result(self):
        return self._result


