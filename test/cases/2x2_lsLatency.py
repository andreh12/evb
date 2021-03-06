import operator

from TestCase import *
from Context import RU,BU


class case_2x2_lsLatency(TestCase):

    def runTest(self):
        testDir="/tmp/evb_test/ramdisk"
        runNumber=time.strftime("%s",time.localtime())
        for instance in range(2):
            buDir = testDir+"/BU"+str(instance)
            self.setAppParam('rawDataDir','string',buDir,'BU',instance)
            self.setAppParam('metaDataDir','string',buDir,'BU',instance)
            self.setAppParam('hltParameterSetURL','string','file://'+buDir,'BU',instance)
        self.prepareAppliance(testDir+"/BU0",runNumber)
        self.writeResourceSummary(testDir+"/BU0",runNumber,activeRunCMSSWMaxLS=3,cloud=32)
        self.prepareAppliance(testDir+"/BU1",runNumber)
        self.writeResourceSummary(testDir+"/BU1",runNumber,activeRunCMSSWMaxLS=3)
        self.configureEvB()
        self.enableEvB(sleepTime=2,runNumber=runNumber)
        self.checkEVM(2048)
        self.checkRU(24576)
        self.checkBU(26624)
        self.waitForAppParam('nbLumiSections','unsignedInt',6,operator.ge,'BU')
        self.checkAppState("Mist","BU",0)
        self.checkAppState("Throttled","BU",1)
        self.waitForAppParam('nbLumiSections','unsignedInt',7,operator.ge,'BU')
        self.checkAppState("Cloud","BU",0)
        self.checkAppState("Blocked","BU",1)
        self.haltEvB()


    def fillConfiguration(self,symbolMap):
        self._config.add( RU(symbolMap,[
             ('inputSource','string','Local'),
             ('fedSourceIds','unsignedInt',(512,)),
             ('fakeLumiSectionDuration','unsignedInt','4')
            ]) )
        self._config.add( RU(symbolMap,[
             ('inputSource','string','Local'),
             ('fedSourceIds','unsignedInt',range(1,13))
            ]) )
        self._config.add( BU(symbolMap,[
            ('resourcesPerCore','double','1'),
            ('staleResourceTime','unsignedInt','0')
            ]) )
        self._config.add( BU(symbolMap,[
            ('resourcesPerCore','double','1'),
            ('staleResourceTime','unsignedInt','0')
            ]) )
