from TestCase import TestCase
from Context import RU,BU


class case_2x1_smallBlockSize(TestCase):

    def runTest(self):
        self.configureEvB()
        self.enableEvB()
        self.checkEVM(2048,100)
        self.checkRU(24576)
        self.checkBU(26624,100)
        self.haltEvB()


    def fillConfiguration(self,symbolMap):
        self._config.add( RU(symbolMap,[
             ('inputSource','string','Local'),
             ('fedSourceIds','unsignedInt',(512,)),
             ('blockSize','unsignedInt','1024')
            ]) )
        self._config.add( RU(symbolMap,[
             ('inputSource','string','Local'),
             ('fedSourceIds','unsignedInt',range(1,13)),
             ('blockSize','unsignedInt','1024')
            ]) )
        self._config.add( BU(symbolMap,[
             ('dropEventData','boolean','true'),
             ('lumiSectionTimeout','unsignedInt','0'),
             ('eventsPerRequest','unsignedInt','8'),
             ('maxEvtsUnderConstruction','unsignedInt','64')
            ]) )
