#    Paperwork - Using OCR to grep dead trees the easy way
#    Copyright (C) 2012  Jerome Flesch
#
#    Paperwork is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Paperwork is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Paperwork.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import threading
import time
import traceback

import gobject

class Worker(gobject.GObject):
    can_interrupt = False

    def __init__(self, name):
        gobject.GObject.__init__(self)
        self.name = name
        self.can_run = True
        self.__thread = None
        self.__started_by = None

    def do(self, **kwargs):
        # implemented by the child class
        #
        # if can_interrupt = True, the child class must check self.can_run as
        # often as possible
        assert()

    def __wrapper(self, **kwargs):
        print "Workers: [%s] started" % (self.name)
        self.do(**kwargs)
        print "Workers: [%s] ended" % (self.name)

    def start(self, **kwargs):
        if self.is_running:
            print "====="
            print "ERROR"
            print "Thread '%s' was already started by:" % (self.name)
            idx = 0
            for stack_el in self.__started_by:
                print ("%2d : %20s : L%5d : %s"
                       % (idx, os.path.basename(stack_el[0]),
                          stack_el[1], stack_el[2]))
                idx += 1
            print "====="
            raise threading.ThreadError(
                ("Tried to start a thread already running: %s"
                 % (self.name)))
        self.__started_by = traceback.extract_stack()
        self.can_run = True
        self.__thread = threading.Thread(target=self.__wrapper, kwargs=kwargs)
        self.__thread.start()

    def soft_stop(self):
        self.can_run = False

    def stop(self):
        print "Stopping worker [%s]" % (self)
        sys.stdout.flush()
        if not self.can_interrupt and self.is_running:
            print ("Trying to stop worker [%s], but it cannot be stopped"
                   % (self.name))
        self.can_run = False
        if self.is_running:
            self.__thread.join()
            assert(not self.is_running)

    def wait(self):
        if not self.is_running:
            return
        self.__thread.join()
        assert(not self.is_running)

    def __get_is_running(self):
        return (self.__thread != None and self.__thread.is_alive())

    is_running = property(__get_is_running)

    def __str__(self):
        return self.name


class WorkerQueue(Worker):
    can_interrupt = True

    __gsignals__ = {
        'queue-start' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
        'queue-stop' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                        # Arg: Exception raised by a worker, None if none
                        (gobject.TYPE_PYOBJECT, )),
    }
    local_signals = ['queue-start', 'queue-stop']

    def __init__(self, name):
        Worker.__init__(self, name)
        self.__queue = []
        self.__current_worker = None
        self.__signals = {}

    def add_worker(self, worker):
        for (signal, (handler, kargs)) in self.__signals.iteritems():
            worker.connect(signal, handler, *kargs)
        self.__queue.append(worker)

    def do(self, **kwargs):
        self.emit('queue-start')
        exception = None
        try:
            try:
                while len(self.__queue) > 0 and self.can_run:
                    self.__current_worker = self.__queue.pop(0)
                    print ("Queue [%s]: Starting worker [%s]"
                           % (self.name, self.__current_worker.name))
                    self.__current_worker.do(**kwargs)
                    print ("Queue [%s]: Worker [%s] has ended"
                           % (self.name, self.__current_worker.name))
            except Exception, exc:
                exception = exc
                raise
        finally:
            self.__current_worker = None
            self.emit('queue-stop', exception)

    def connect(self, signal, handler, *kargs):
        if signal in self.local_signals:
            Worker.connect(self, signal, handler, *kargs)
            return
        self.__signals[signal] = (handler, kargs)
        for worker in self.__queue:
            worker.connect(signal, handler, *kargs)

    def stop(self):
        if self.__current_worker != None:
            self.__current_worker.stop()
        Worker.stop(self)

gobject.type_register(WorkerQueue)


class WorkerProgressUpdater(Worker):
    """
    Update a progress bar a predefined timing.
    """

    can_interrupt = True

    NB_UPDATES = 50

    def __init__(self, name, progressbar):
        self.name = "Progress bar updater: %s" % (name)
        Worker.__init__(self, self.name)
        self.progressbar = progressbar

    def do(self, value_min=0.0, value_max=0.5, total_time=20.0):
        for upd in range(0, self.NB_UPDATES):
            if not self.can_run:
                return
            val = value_max - value_min
            val *= upd
            val /= self.NB_UPDATES
            val += value_min

            gobject.idle_add(self.progressbar.set_fraction, val)
            time.sleep(total_time / self.NB_UPDATES)


gobject.type_register(WorkerProgressUpdater)
