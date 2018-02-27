#!/usr/bin/env python

import argparse
import os
import subprocess
import sys
import time

import messengers
from SymbolMap import SymbolMap
from TestCase import TestCase


class BadConfig(Exception):
    pass


class Tee(object):
    def __init__(self, *files):
        self._files = files

    def write(self, obj):
        for f in self._files:
            f.write(obj)

    def flush(self):
         for f in self._files:
            f.flush()


class TestRunner:

    def __init__(self):
        try:
            self._evbTesterHome = os.environ["EVB_TESTER_HOME"]
        except KeyError:
            print("Please specify the test directory to be used in the environment veriable EVB_TESTER_HOME")
            sys.exit(2)

        # the launcher script to be executed on the remote host
        # check whether it exists (assuming a cluster wide file system) 
        # or not before attempting to launch it on the remote hosts
        self._launcherScript = self._evbTesterHome + "/scripts/xdaqLauncher.py"
        if not os.path.exists(self._launcherScript):
            print("Could not find xdaq launcher script " + self._launcherScript + ".")
            print("Does the environment variable EVB_TESTER_HOME point to the correct directory ?")
            sys.exit(2)



    def addOptions(self,parser):
        parser.add_argument("-v","--verbose",action='store_true',help="print log info also to stdout")
        parser.add_argument("--numa",action='store_false',help="do not use NUMA settings")
        parser.add_argument("-l","--launchers",choices=('start','stop'),help="start/stop xdaqLaunchers")
        parser.add_argument("--logDir",default=self._evbTesterHome+'/log/',help="log directory [default: %(default)s]")
        parser.add_argument("--dummyXdaq", action = 'store_true', default = False, help="run dummyXdaq.py instead of xdaq.exe (useful for development)")

    def run(self,args):
        self.args = vars(args)
        #print(self.args)
        #return
        try:
            os.mkdir(self.args['logDir'])
        except OSError:
            pass
        try:
            self.doIt()
        except KeyboardInterrupt:
            pass


    def startLaunchers(self):
        
        launcherCmd = "cd /tmp && rm -f /tmp/core.* && export XDAQ_ROOT="+os.environ["XDAQ_ROOT"]+" && "+ self._launcherScript + " "
        if not self.args['verbose']:
            launcherCmd += "--logDir "+self.args['logDir']+" "
        if self.args['numa']:
            launcherCmd += "--useNuma "

        if self.args['dummyXdaq']:
            launcherCmd += "--dummyXdaq "

        for launcher in self._symbolMap.launchers:
            if self.args['verbose']:
                print("Starting launcher on "+launcher[0]+":"+str(launcher[1]))
            subproc = subprocess.Popen(["ssh",

                              # avoid ssh waiting for confirmation of unknown host key
                              # but keep keys learned this way in a separate file
                              # similar to what wassh does by default
                              "-o","UserKnownHostsFile=" + os.path.expanduser("~/.evbtest_known_hosts"),
                              "-o","StrictHostKeyChecking=no",

                              "-x","-n",launcher[0],launcherCmd+str(launcher[1])])

            # avoid the ssh process surviving the end of this program
            # (see e.g. https://stackoverflow.com/a/11366424/288875 why we need
            # a default value for the lambda function)
            import atexit
            atexit.register(lambda proc = subproc: proc.kill())

    def stopLaunchers(self):
        for launcher in self._symbolMap.launchers:
            if self.args['verbose']:
                print("Stopping launcher on "+launcher[0]+":"+str(launcher[1]))

            import xmlrpclib
            server = xmlrpclib.ServerProxy("http://%s:%s" % (launcher[0],launcher[1]))
            server.stopLauncher()
