#!/usr/bin/env python

import time, sys, os
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))

from TestCase import TestCase
from RestartableRunner import RestartableRunner


class RestartableRunnerRunBenchmarks(RestartableRunner):

    def getConfigAndStartLaunchers(self):

        self.testRunner.startLaunchers()
        time.sleep(1)

        return self.testRunner.getAllConfigurations()[0]
    
    def runSpecific(self, stdout, config, testName):
        self.testCase = TestCase(config, stdout, afterStartupCallback=self.afterStartupCallback)
        self.testCase.prepare(testName)

        fragSize = self.testRunner.getFedSizes()
        assert len(fragSize) == 1

        fragSize = fragSize[0]
        fragSizeRMS = int(fragSize * self.testRunner.args['rms'])

        # this should only terminate when the user terminates the optimization
        self.testCase.runScan(fragSize, fragSizeRMS, self.testRunner.args)
        
