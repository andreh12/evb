import sys
import time

import messengers
from TestCase import *


class ConfigCase(TestCase):

    def __init__(self,config,stdout,fedSizeScaleFactors,defaultFedSize,afterStartupCallback = None):
        TestCase.__init__(self,config,stdout, afterStartupCallback = afterStartupCallback)
        self.fedSizeScaleFactors = fedSizeScaleFactors
        self.defaultFedSize = defaultFedSize


    def destroy(self):
        TestCase.destroy(self)


    def calculateFedSize(self,fedId,fragSize,fragSizeRMS):
        if len(self.fedSizeScaleFactors):
            try:
                (a,b,c,rms) = self.fedSizeScaleFactors[fedId]
                relSize = fragSize / self.defaultFedSize
                fedSize = a + b*relSize + c*relSize*relSize
                fedSizeRMS = fedSize * rms
                return (int(fedSize+4)&~0x7,int(fedSizeRMS+4)&~0x7)
            except KeyError:
                if fedId != '0xffffffff':
                    print("Missing scale factor for FED id "+fedId)
        else:
            return TestCase.calculateFedSize(self,fedId,fragSize,fragSizeRMS)
