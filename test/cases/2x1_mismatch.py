import operator
import time

from TestCase import *
from Context import FEROL,RU,BU


class case_2x1_mismatch(TestCase):

    def checkIt(self):
        self.checkEVM(8192)
        self.checkRU(8192)
        self.checkBU(16384)


    def runTest(self):
        self.configureEvB()
        self.enableEvB(runNumber=1)
        self.checkIt()

        sys.stdout.write("Skipping an event on FED 2")
        sys.stdout.flush()
        self.setAppParam('skipNbEvents','unsignedInt','1','FEROL',2)
        self.waitForAppState("SyncLoss","EVM")
        print(" done")
        self.checkAppState("Enabled","RU")
        self.checkAppState("Enabled","BU")
        self.checkAppParam('eventRate','unsignedInt',0,operator.eq,"EVM")
        self.checkAppParam('fragmentRate','unsignedInt',0,operator.eq,"FEROL")
        dumps = self.getFiles("dump_run000001_event[0-9]+_fed[0-9]+.txt$",app="EVM")
        if len(dumps) != 1:
            raise ValueException("Expected one FED dump file, but found: "+str(dumps))
        self.haltEvB()
        time.sleep(1)

        self.configureEvB()
        self.enableEvB(runNumber=2)
        self.checkIt()

        sys.stdout.write("Duplicate an event on FED 1")
        sys.stdout.flush()
        self.setAppParam('duplicateNbEvents','unsignedInt','1','FEROL',1)
        self.waitForAppState("SyncLoss","EVM")
        print(" done")
        self.checkAppState("Enabled","RU")
        self.checkAppState("Enabled","BU")
        self.checkAppParam('eventRate','unsignedInt',0,operator.eq,"EVM")
        self.checkAppParam('fragmentRate','unsignedInt',0,operator.eq,"FEROL")
        dumps = self.getFiles("dump_run000002_event[0-9]+_fed[0-9]+.txt$",app="EVM")
        if len(dumps) != 1:
            raise ValueException("Expected one FED dump file, but found: "+str(dumps))
        self.haltEvB()
        time.sleep(1)

        self.configureEvB()
        self.enableEvB(runNumber=3)
        self.checkIt()

        sys.stdout.write("Skipping an event on FED 5")
        sys.stdout.flush()
        self.setAppParam('skipNbEvents','unsignedInt','1','FEROL',5)
        self.waitForAppState("SyncLoss","RU")
        print(" done")
        self.checkAppState("Enabled","EVM")
        self.checkAppState("Enabled","BU")
        self.checkAppParam('eventRate','unsignedInt',0,operator.eq,"EVM")
        self.checkAppParam('fragmentRate','unsignedInt',0,operator.eq,"FEROL")
        dumps = self.getFiles("dump_run000003_event[0-9]+_fed[0-9]+.txt$",app="RU")
        if len(dumps) != 1:
            raise ValueException("Expected one FED dump file, but found: "+str(dumps))
        self.haltEvB()
        time.sleep(1)

        self.configureEvB()
        self.enableEvB(runNumber=4)
        self.checkIt()

        sys.stdout.write("Duplicate an event on FED 4")
        sys.stdout.flush()
        self.setAppParam('duplicateNbEvents','unsignedInt','1','FEROL',4)
        self.waitForAppState("SyncLoss","RU")
        print(" done")
        self.checkAppState("Enabled","EVM")
        self.checkAppState("Enabled","BU")
        self.checkAppParam('eventRate','unsignedInt',0,operator.eq,"EVM")
        self.checkAppParam('fragmentRate','unsignedInt',0,operator.eq,"FEROL")
        dumps = self.getFiles("dump_run000004_event[0-9]+_fed[0-9]+.txt$",app="RU")
        if len(dumps) != 1:
            raise ValueException("Expected one FED dump file, but found: "+str(dumps))
        self.haltEvB()
        time.sleep(1)

        self.configureEvB()
        self.enableEvB(runNumber=5)
        self.checkIt()

        sys.stdout.write("Skipping an event on FED 0")
        sys.stdout.flush()
        self.setAppParam('skipNbEvents','unsignedInt','1','FEROL',0)
        self.waitForAppState("SyncLoss","EVM")
        print(" done")
        self.checkAppState("Enabled","RU")
        self.checkAppState("Enabled","BU")
        self.checkAppParam('eventRate','unsignedInt',0,operator.eq,"EVM")
        self.checkAppParam('fragmentRate','unsignedInt',0,operator.eq,"FEROL")
        dumps = self.getFiles("dump_run000005_event[0-9]+_fed[0-9]+.txt$",app="EVM")
        if len(dumps) != 1:
            raise ValueException("Expected one FED dump file, but found: "+str(dumps))
        self.haltEvB()
        time.sleep(1)

        self.configureEvB()
        self.enableEvB(runNumber=6)
        self.checkIt()

        sys.stdout.write("Duplicate an event on FED 0")
        sys.stdout.flush()
        self.setAppParam('duplicateNbEvents','unsignedInt','1','FEROL',0)
        self.waitForAppState("SyncLoss","EVM")
        print(" done")
        self.checkAppState("Enabled","RU")
        self.checkAppState("Enabled","BU")
        self.checkAppParam('eventRate','unsignedInt',0,operator.eq,"EVM")
        self.checkAppParam('fragmentRate','unsignedInt',0,operator.eq,"FEROL")
        dumps = self.getFiles("dump_run000006_event[0-9]+_fed[0-9]+.txt$",app="EVM")
        if len(dumps) != 1:
            raise ValueException("Expected one FED dump file, but found: "+str(dumps))
        self.haltEvB()


    def fillConfiguration(self,symbolMap):
        evm = RU(symbolMap,[
             ('inputSource','string','Socket'),
             ('checkCRC','unsignedInt','0')
            ])
        for id in range(0,4):
            self._config.add( FEROL(symbolMap,evm,id) )

        ru = RU(symbolMap,[
             ('inputSource','string','Socket'),
             ('checkCRC','unsignedInt','0')
            ])
        for id in range(4,8):
            self._config.add( FEROL(symbolMap,ru,id) )

        self._config.add( evm )
        self._config.add( ru )

        self._config.add( BU(symbolMap,[
             ('dropEventData','boolean','true'),
             ('lumiSectionTimeout','unsignedInt','0')
            ]) )
