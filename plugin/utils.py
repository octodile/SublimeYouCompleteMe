# Copyright (C) 2014 Ivan Koster
# 
# This file is part of SublimeYouCompleteMe.
# 
# SublimeYouCompleteMe is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# SublimeYouCompleteMe is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with SublimeYouCompleteMe.  If not, see <http://www.gnu.org/licenses/>.

""" A collection of handy helper functions """
import collections
import json
import sys
import os
import socket
from threading import Thread, Event

from . import settings

WIN_PYTHON27_PATH = "C:\\python27\\python.exe" #TODO pythonw

def get_unused_localhost_port():
    """ Get a free port number """
    sock = socket.socket()
    sock.bind(( '', 0 ))
    port = sock.getsockname()[1]
    sock.close()
    return port

def to_utf8_if_needed(obj):
    if isinstance(obj, bytes):
        return obj.encode("utf-8")
    if isinstance(obj, str):
        return obj
    return str(obj)

def encode_unicode_to_utf8(data):
    """ Encode data to utf8. Also recurses into iterables and dicts and converts
    those contents also to utf8
    """
    if isinstance(data, bytes):
        return data.encode("utf-8")
    if isinstance(data, str):
        return data
    elif isinstance(data, collections.Mapping):
        return dict(map(encode_unicode_to_utf8, data.items()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(encode_unicode_to_utf8, data))
    else:
        return data


def to_utf8_json(data):
    """ Converts data to utf8 recursively and then converts it to json """
    return json.dumps(encode_unicode_to_utf8(data),
                      ensure_ascii=False)

def on_windows():
    """ Are we on windows? """
    return sys.platform == 'win32'


def path_to_python():
    """ Get path to python interpreter """
    # TODO
    # path = settings.SETTINGS.get("path_to_python_27")
    path = None

    if path:
        return path

    if on_windows():
        if os.path.exists(WIN_PYTHON27_PATH):
            return WIN_PYTHON27_PATH

    path = path_to_first_existing_executable(["python2", "python"])
    if path:
        return path

    raise RuntimeError("Could not find python 2.7!")


def path_to_first_existing_executable(executable_name_list):
    """ Given a list of executables, return the first one found on the PATH """
    for executable_name in executable_name_list:
        path = find_executable(executable_name)
        if path:
            return path
    return None

def find_executable(executable, path=None):
    """ Copied from disutils.spawn from the python standard library, because
    sublime text doesn't seem to ship it.
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    base, ext = os.path.splitext(executable)

    if (sys.platform == 'win32' or os.name == 'os2') and (ext != '.exe'):
        executable = executable + '.exe'

    if not os.path.isfile(executable):
        for p in paths:
            f = os.path.join(p, executable)
            if os.path.isfile(f):
                # the file exists, we have a shot at spawn working
                return f
        return None
    else:
        return executable


def TimerReset(*args, **kwargs):
    """Factory function to create a resettable Timer object.

    Timers call a function after a specified number of seconds:

        t = TimerReset(30.0, f, args=[], kwargs={})
        t.start()
        t.cancel()     # stop the timer's action if it's still waiting

    """
    return _TimerReset(*args, **kwargs)


class _TimerReset(Thread):
    """Call a function after a specified number of seconds:

            t = TimerReset(30.0, f, args=[], kwargs={})
            t.start()
            t.cancel()     # stop the timer's action if it's still waiting
        The timer (while it is running) can be reset with t.reset()
    """

    def __init__(self, interval, function, args=[], kwargs={}):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.finished = Event()
        self.must_wait = True

    def cancel(self):
        """Stop the timer if it hasn't finished yet"""
        self.finished.set()

    def run(self):
        while self.must_wait:
            self.must_wait = False
            self.finished.wait(self.interval)

        if not self.finished.isSet():
            self.function(*self.args, **self.kwargs)
        self.finished.set()

    def reset(self, interval=None):
        """ Reset the timer """
        assert self.isAlive

        if interval:
            self.interval = interval
        else:
            pass # Keep interval the same

        self.must_wait = True
        self.finished.set()
        self.finished.clear()
