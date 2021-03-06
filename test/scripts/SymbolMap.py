import os
import re
import socket
import sys

class SymbolMap:

    def __init__(self,symbolMapfile):

        # name of the host we are running on
        self._hostname = socket.gethostbyaddr(socket.gethostname())[0]
        self._map = {}
        self.launchers = []

        # maps from strings like 'RU' to a list of host types
        self._shortHostTypeToHostTypes = {}

        hostTypeRegEx = re.compile('^([A-Za-z0-9_]+)SOAP_HOST_NAME')

        # similar to hostTypeRegEx but only capturing RU, BU etc.
        shortHostTypeRegEx = re.compile('^([A-Za-z]+)[0-9]+_')
        hostCount = 0
        launcherPort = None
        previousVal = ""

        try:
            with open(symbolMapfile) as symbolMap:
                for line in symbolMap:
                    if line.rstrip(): #skip empty lines
                        try:
                            (key,val) = line.split()
                            if val == 'localhost':
                                val = self._hostname
                            self._map[key] = val
                            if key == 'LAUNCHER_BASE_PORT':
                                launcherPort = int(val)
                            try:
                                # hostType is e.g. 'BU2_'
                                hostType = hostTypeRegEx.findall(key)[0]

                                shortHostType = shortHostTypeRegEx.findall(key)[0]

                                self._shortHostTypeToHostTypes.setdefault(shortHostType,[]).append(re.sub("_$", "",hostType))

                                if val != previousVal:
                                    launcherPort += 1
                                    self.launchers.append((self._map[hostType + 'SOAP_HOST_NAME'],launcherPort))
                                    previousVal = val

                                self._map[hostType + 'LAUNCHER_PORT'] = str(launcherPort)
                                self._map[hostType + 'SOAP_PORT']     = str(int(self._map['SOAP_BASE_PORT'])     + hostCount)
                                self._map[hostType + 'I2O_PORT']      = str(int(self._map['I2O_BASE_PORT'])      + hostCount)
                                self._map[hostType + 'FRL_PORT']      = str(int(self._map['FRL_BASE_PORT'])      + hostCount)
                                self._map[hostType + 'FRL_PORT2']     = str(int(self._map['FRL_BASE_PORT']) + 50 + hostCount)
                                hostCount += 1
                            except IndexError:
                                pass
                        except ValueError:
                            pass

        except EnvironmentError as e:
            print("Could not open "+symbolMapfile+": "+str(e))
            sys.exit(2)


    def getHostInfo(self,hostType):
        """
        :param hostType: is a string like "BU2" (i.e. application type including 'instance' number)
        :return: a dict with information about the given instance of an application type
        """
        hostInfo = {'launcherPort':self._map[hostType + '_LAUNCHER_PORT'],
                    'soapHostname':self._map[hostType + '_SOAP_HOST_NAME'],
                    'soapPort':self._map[hostType + '_SOAP_PORT']}
        try:
            hostInfo['i2oHostname'] = self._map[hostType + '_I2O_HOST_NAME']
            hostInfo['i2oPort'] = self._map[hostType + '_I2O_PORT']
        except KeyError:
            pass
        try:
            hostInfo['frlHostname'] = self._map[hostType + '_FRL_HOST_NAME']
            hostInfo['frlPort'] = self._map[hostType + '_FRL_PORT']
            hostInfo['frlPort2'] = self._map[hostType + '_FRL_PORT2']
        except KeyError:
            pass
        return hostInfo

    def getHostsOfType(self, shortHostType):
        """
        :param shortHostType: a 'short host type' like 'BU'
        :return: a list of 'host types' like 'BU2' for the given short host type
         or an empty list if no entry for the given type was found
        """

        return self._shortHostTypeToHostTypes.get(shortHostType, [])

    def getShortHostTypes(self):
        """
        :return: a list of know 'short host types'
        """
        return list(self._shortHostTypeToHostTypes)

    def parse(self,string):
        for (key,val) in self._map.iteritems():
            string = string.replace(key,val)
        return string



if __name__ == "__main__":

    symbolMap = SymbolMap(os.environ["EVB_TESTER_HOME"]+"/cases/standaloneSymbolMap.txt")
    print(symbolMap._map)
    print(symbolMap.launchers)
