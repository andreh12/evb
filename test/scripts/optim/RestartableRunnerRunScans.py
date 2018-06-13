#!/usr/bin/env python

import time, sys, os

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))
from ConfigCase import ConfigCase
from RestartableRunner import RestartableRunner

class RestartableRunnerRunScans(RestartableRunner):
    
    def getConfigAndStartLaunchers(self):

        # ensure the fedsizes are set
        self.testRunner.fillFedSizeScalesFromFile()

        configData = self.testRunner.getAllConfigurations()[0]
        self.testRunner._symbolMap = configData['config'].symbolMap

        self.testRunner.startLaunchers()
        time.sleep(1)

        return configData

    def runSpecific(self, stdout, config, testName):
        #----------
        # borrowed from RunScans.runConfig()
        #----------
        assert len(self.testRunner.getFedSizes()) == 1, "must have exactly one FED size for this optimization"

        self.testCase = ConfigCase(config, stdout,
                                   self.testRunner.fedSizeScaleFactors, 
                                   self.testRunner.defaultFedSize,
                                   afterStartupCallback = self.afterStartupCallback)
        self.testCase.setXdaqLogLevel(self.testRunner.args['logLevel'])
        self.testCase.prepare(testName)
        #----------

        # this should only terminate when the user terminates the optimization
        self.testCase.runConfig(testName, config, stdout)

