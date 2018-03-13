#!/usr/bin/env python

import re

#----------------------------------------------------------------------

def getWorkLoops(xdaqHostPort):
    # @param xdaqHostPort is a tuple (host, port)
    # where the mapping of work loop names to
    # lightweight process id can be retrieved
    # 
    # queries the remote host and 
    # returns a mapping of worker loop names to pids
    # (dict with worker thread name to dict with a key 'pid')

    import urllib2, json
    fin = urllib2.urlopen("http://%s:%d/urn:xdaq-application:service=hyperdaq/workLoopList" % (xdaqHostPort[0], xdaqHostPort[1]))
    txt = fin.read()
    
    fin.close()

    return json.loads(txt)

#----------------------------------------------------------------------

def getFedIdsFromWorkLoopNames(workLoopNames):
    # returns a sorted list of the FEDids found in the given
    # work loop names
    fedids = set()

    for name in workLoopNames:
        mo = re.match('evb::RU_\d+/parseSocketBuffers_(\d+)/waiting$', name)
        if mo:
            fedids.add(int(mo.group(1)))
    
    return sorted(fedids)
    
#----------------------------------------------------------------------

def canonicalizeWorkLoopNames(workLoopNames):
    # returns a mapping of original workloop name 
    # to a canonical workloop name (removing RU and BU numbers,
    # replace FED ids etc.).
    #
    # only leaves those work loop names which we want to tune

    result = {}

    mappedNames = set()

    fedids = getFedIdsFromWorkLoopNames(workLoopNames)

    for wln in workLoopNames:
        for pattern in (
            # matching groups in parentheses in the regex patterns
            # below will be removed

            # close to 100% CPU usage threads        
            'pt::ibv::completionworkloopr(-\d+)/polling', # found on BU and RU
            'pt::ibv::completionworkloops/polling',       # found on BU and RU
            'tcpla-psp/(\S+:)\d+/polling',                # found on RU; remove host name but keep the port number

            # 60-70% CPU:
            'evb::RU(_\d+)/parseSocketBuffers_(\d+)/waiting',  # found on RU
            'evb::RU(_\d+)/Responder_\d+/waiting',           # found on RU
            'evb::RU(_\d+)/parseSocketBuffers_\d+/waiting',  # found on RU

            'evb::BU(_\d+)/Builder_\d+/waiting',             # found on BU

            # < 10% CPU usage
            'fifo/PeerTransport/waiting',                    # found on BU and RU
            'evb::RU(_\d+)/buPoster/waiting',                # found on RU
            'evb::RU(_\d+)/Pipe(_\S+):\d+/waiting',          # found on RU; remove host name but keep port number

            'evb::BU(_\d+)/requestFragments/waiting',        # found on BU
            'evb::BU(_\d+)/lumiAccounting/waiting',          # found on BU
            ):

            pattern = pattern + "$"

            mo = re.match(pattern, wln)

            if mo:
                # keep this workloop

                newName = ""

                # replace all matching groups with empty strings
                prevEnd = 0
                for index in range(1, len(mo.groups()) + 1):
                    newName += wln[prevEnd:mo.start(index)]
                    
                    if index == 2 and 'parseSocketBuffers' in wln:
                        # special treatment for work loop names containing FED ids
                        fedid = int(mo.group(index))
                        
                        fedIndex = fedids.index(fedid)
                        newName += "%02d" % fedIndex

                    prevEnd = mo.end(index)

                newName += wln[prevEnd:]
                
                # make sure newName has not been produced before
                assert not newName in mappedNames
                mappedNames.add(newName)

                result[wln] = newName

                break
            # if thread of interest
        # loop over patterns
    # loop over workloop name

    return result

#----------------------------------------------------------------------

class WorkLoopData:
    # contains information about the workloops of a single 
    # XDAQ process on a given host

    #----------------------------------------
    
    def __init__(self, appType, soapHost, soapPort, launcherPort):
        # @param appType is 'RU', 'BU' or 'RUBU'
        # @param launcherPort is the port where to contact
        # the launcher to set the pinning of a process

        self.appType = appType

        # fetch the information about the workloops
        workerList = getWorkLoops((soapHost, soapPort))

        # canonicalize work loop names
        wlnToCanonical = canonicalizeWorkLoopNames(workerList.keys())

        # keep a list of unused workloops for debugging purposes
        self.unusedWorkLoops = sorted(
            [ wln 
              for wln in workerList.keys()
              if not wln in wlnToCanonical.keys()              
              ])


        # maps from canonical workloop name
        # to process id on the soapHost
        self.workLoopToPid = {}

        for wln, cwln in wlnToCanonical.items():
            self.workLoopToPid[cwln] = workerList[wln]['SYS_gettid']

        # create an xmlrpc client
        import xmlrpclib

        self.rpcclient = xmlrpclib.ServerProxy("http://%s:%s" % (soapHost, launcherPort))

    #----------------------------------------

    def getCanonicalWorkLoopNames(self):
        return self.workLoopToPid.keys()

    #----------------------------------------

    def pinThread(self, canonicalWorkLoopName, core):
        # pin the process to the given core
        pid = self.workLoopToPid[canonicalWorkLoopName]
        self.rpcclient.pinProcess(pid, core)

    #----------------------------------------

#----------------------------------------------------------------------
