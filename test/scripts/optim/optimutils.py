#!/usr/bin/env python

import time
import logging
import sys, re

#----------------------------------------------------------------------

def initLogging(fnameTemplate, timestamp):
    # setup logging
    # see e.g. https://stackoverflow.com/a/14058475/288875
    #
    # @param fnameTemplate the template for the name of the log
    # file. {timestamp} will be replaced by the timestamp value.
    # 
    # @param timestamp can be None in which case the current time
    # is used
    if timestamp is None:
        timestamp = time.strftime("%Y-%m-%d-%H%M%S")

    logFname = fnameTemplate.format(timestamp = timestamp)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.FileHandler(logFname)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    root.addHandler(ch)

    return timestamp

#----------------------------------------------------------------------

