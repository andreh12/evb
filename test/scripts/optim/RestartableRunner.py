#!/usr/bin/env python

import threading, logging, time, sys, os

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))
from TestRunner import BadConfig
from TestCase import TestCase
from TestCase import FailedState, StateException

class RestartableRunner:
    """class for running a single configuration without writing out
    any results. Can be asked to restart stop and restart the EVB."""

    def __init__(self, testRunner):
        # @param testRunner is used to get the requested
        #        EVB configuration. It should inherit
        #        from class TestRunner and have a method
        #        getConfiguration()

        self.testRunner = testRunner

        # flag whether EVB should be restarted
        # after it was stopped or not
        self.stopFlag = False

        # flag for 'evb was started'
        self.evbStarted = threading.Event()
        self.evbStopped = threading.Event()
        self.evbStopped.set()

        # queues for communication with
        # callback which is called after
        # the startup of the EVB
        from Queue import Queue

        # used to signal that the EVB should be stopped
        self.stopQueue = Queue()

        # acknowledgement events that EVB was stopped
        self.stopAckQueue = Queue()

        # callback which is called after a TestCaseObject was created
        self.beforeScanStartCallback = None

        self.testCase = None

    def runSpecific(self, stdout, config, testName):
        """benchmark-specific implementation of how to run the test"""
        raise Exception("must override this method")

    def getConfigAndStartLaunchers(self):
        """benchmark-specific implementation of how to retrieve
        the (first) configuration and start launchers if necessary 
        """
        raise Exception("must override this method")        

    def run(self, stdout):

        logging.info("RestartableRunner.run() called")

        configData = self.getConfigAndStartLaunchers()

        config = configData['config']
        testName = configData['name']

        try:
            while not self.stopFlag:
                try:

                    # call benchmark specific implementation
                    # to start the tests
                    self.runSpecific(stdout, config, testName)

                    # evb was stopped
                    self.evbStarted.clear()
                    self.evbStopped.set()

                    self.testCase.destroy()
                    self.testCase = None

                except BadConfig:
                    self.stopFlag = True
                    sys.exit(1)
        finally:
            self.testRunner.stopLaunchers()



    def checkApplicationsEnabled(self):
        # @return true if all applications are in 'Enabled' state
        # note that this gives only meaningful results
        # while run() is running

        if not self.testCase is None:
            try:
                self.testCase.checkState('Enabled')
                return True
            except (StateException, FailedState), ex:
                # some are not in Enabled state
                return False

        return None


    def afterStartupCallback(self, configCase):
        """callback which is called after startup of the EVB.
        When this function returns, the EVB will be stopped by
        the calling function.
        """

        # This method is called in ConfigCase.doIt()
        # after the EVB was successfully started.
        # Once we return from this function, the
        # EVB is stopped

        # signal that the EVB was started
        self.evbStarted.set()
        self.evbStopped.clear()

        # wait for stop command
        self.stopQueue.get()

        # achknowledge stop command
        self.stopAckQueue.put(True)

        # after returning from this function the EVB will be stopped



    def stopEVB(self):
        """function to be called from outside to stop the EVB restarting
        loop (e.g. call this when CTRL-C was pressed)"""

        logging.info("stopping EVB")

        # avoid automatic restart
        self.stopFlag = True

        # signal stop
        self.stopQueue.put(True)

        logging.info("stopping EVB complete")



    def restartEVB(self):
        """
        signals to the callback to stop waiting
        and then signals to the running thread
        to start another iteration.

        This function must only be called
        when the EVB is currently running.
        """

        logging.info("restarting EVB")

        # ensure restarting
        self.stopFlag = False

        # signal stop
        self.stopQueue.put(True)

        # and wait for stopping acknowledged
        self.evbStopped.wait()
        logging.info("stopping EVB complete")

        # wait for restart complete
        self.evbStarted.wait()
        logging.info("restarting EVB complete")

