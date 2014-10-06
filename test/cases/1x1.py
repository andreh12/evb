from time import sleep
from TestCase import TestCase
from Configuration import RU,BU


class case_1x1(TestCase):

    def runTest(self):
        self.configureEvB()
        self.enableEvB()
        sleep(10)
        self.checkEVM(2048)
        self.checkBU(2048)
        self.stopEvB()
        self.haltEvB()


    def fillConfiguration(self,symbolMap):
        self._config.add( RU(symbolMap,
            [('inputSource','string','Local'),
             ('fedSourceIds','unsignedInt',(512,))
            ]) )
        self._config.add( BU(symbolMap,
            [('dropEventData','boolean','true')
            ]) )