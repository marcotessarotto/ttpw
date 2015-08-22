#!/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import treetaggerwrapper as ttpw


__all__ = []


# ==============================================================================
class TaggerPoll(object):
    """Keep a poll of TreeTaggers for processing with different threads.

    This class is here for people preferring natural language processing
    over multithread programming… :-)

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
    def __init__(self, workerscount=None, taggerscount=None, **kwargs):
        """Creation of a new TaggerPoll.

        By default a :class:`TaggerPoll` creates same count of threads and
        of TreeTagger objects than there are CPU cores on your computer.

        :param workerscount: number of worker threads to create.
        :type workerscount: int
        :param taggerscount: number of TreeTaggers objects to create.
        :type taggerscount: int
        :param kwargs: same parameters as :func:`TreeTagger.__init__`.
        """
        if workerscount is None:
            workerscount = multiprocessing.cpu_count()
        if taggerscount is None:
            taggerscount = multiprocessing.cpu_count()
        # Security, we need at least one worker and one tagger.
        if taggerscount < 1:
            raise ValueError("Invalid taggerscount %s", taggerscount)
        if workerscount < 1:
            raise ValueError("Invalid workerscount %s", workerscount)

        if DEBUG_MULTITHREAD:
            logger.debug("Creating TaggerPoll, %d workers, %d taggers",
                         workerscount,taggerscount )

        self._stopping = False
        self._workers = []
        self._waittaggers = queue.Queue()
        self._waitjobs = queue.Queue()

        self._build_taggers(taggerscount, kwargs)
        self._build_workers(workerscount)

        if DEBUG_MULTITHREAD:
            logger.debug("TaggerPoll ready")

    def _build_taggers(self, taggerscount, taggerargs):
        if DEBUG_MULTITHREAD:
            logger.debug("Creating taggers for TaggerPoll")
        for i in range(taggerscount):
            tt = TreeTagger(**taggerargs)
            self._waittaggers.put(tt)

    def _build_workers(self, workerscount):
        if DEBUG_MULTITHREAD:
            logger.debug("Creating workers for TaggerPoll")
        for i in range(workerscount):
            th = threading.Thread(target=self._worker_main)
            th.daemon = True
            self._workers.append(th)
            th.start()

    def _create_job(self, methname, **kwargs):
        if self._stopping:
            raise TreeTaggerError("TaggerPoll is stopped working.")
        job = Job(self, methname, kwargs)
        if DEBUG_MULTITHREAD:
            logger.debug("Job %d created, queuing it", id(job))
        self._waitjobs.put(job)
        return job

    def _worker_main(self):
        while True:
            if DEBUG_MULTITHREAD:
                logger.debug("Worker waiting for job to pick…")
            job = self._waitjobs.get()  # Pickup a job.
            if job is None:
                if DEBUG_MULTITHREAD:
                    logger.debug("Worker finishing")
                break   # Put Nones in jobs queue to stop workers.
            if DEBUG_MULTITHREAD:
                logger.debug("Worker doing picked job %d", id(job))
            job._execute()                       # Do the job

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
            # Put one None by thread (will awake threads).
            for x in range(len(self._workers)):
                self._waitjobs.put(None)
        # Wait for threads to be finished.
        for th in self._workers:
            if DEBUG_MULTITHREAD:
                logger.debug("Signaling to thread %s (%d)", th.name, id(th))
            th.join()
        # Remove refs to threads.
        if hasattr(self, '_workers'):
            del self._workers
        # Remove references to TreeTagger objects.
        if hasattr(self, '_waittaggers'):
            del self._waittaggers
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
    def tag_file_async(self, infilepath, encoding=USER_ENCODING,
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
    def tag_file_to_async(self, infilepath, outfilepath, encoding=USER_ENCODING,
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

    def _execute(self):
        # Pickup a tagger.
        logger.debug("Job %d waitin for a tagger", id(self))
        tagger = self._poll._waittaggers.get()
        if DEBUG_MULTITHREAD:
            logger.debug("Job %d picked tagger %d for %s", id(self),
                         id(tagger), self._methname)
        try:
            meth = getattr(tagger, self._methname)
            self._result = meth(**self._kwargs)
        except Exception as e:
            if DEBUG_MULTITHREAD:
                logger.debug("Job %d exit with exception", id(self))
            self._result = e
        # Release the tagger, signal the Job end of processing.
        if DEBUG_MULTITHREAD:
            logger.debug("Job %d give back tagger %d", id(self),
                         id(tagger))
        self._poll._waittaggers.put(tagger)
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


