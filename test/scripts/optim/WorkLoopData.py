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

        for pattern in [
            'evb::RU_\d+/parseSocketBuffers_(\d+)/waiting$',
            'evb::RU_\d+/generating_(\d+)/waiting$',
            ]: 

            mo = re.match(pattern, name)
            if mo:
                fedids.add(int(mo.group(1)))
                break
    
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
            'pt::ibv::completionworkloopr(-\d+)/polling', # found on BU and RU and EVM
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

            # this thread appears when generating on the RU
            # and should be seen as a replacement 
            # for the parseSocketBuffers threads
            "evb::RU(_\d+)/generating_(\d+)/waiting",

            # EVM threads
            "evb::EVM(_\d+)/Responder_(\d+)/waiting",
            "evb::EVM(_\d+)/generating_(\d+)/waiting",
            "evb::EVM(_\d+)/buPoster/waiting",
            "evb::EVM(_\d+)/processRequests/waiting",
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

                    if index == 2:
                        if ('parseSocketBuffers' in wln or 'generating_' in wln) and not 'EVM' in wln:
                            # special treatment for work loop names containing FED ids
                            fedid = int(mo.group(index))

                            fedIndex = fedids.index(fedid)
                            newName += "%02d" % fedIndex
                        else:
                            # on EVM the number in 'generating' seems not to be a FED id ?
                            newName += mo.group(index)

                    prevEnd = mo.end(index)

                newName += wln[prevEnd:]
                
                # make sure newName has not been produced before
                assert not newName in mappedNames, "mapped name %s found more than once" % newName
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

        self.appType  = appType
        self.soapHost = soapHost
        self.soapPort = soapPort

        # list of work loops and associated information
        self.workerList = None

        # maps from work loop name to canonical work loop name
        self.wlnToCanonical = None

        # list of unused work loops (for debugging purposes)
        self.unusedWorkLoops = None

        # keep a list of unused workloops for debugging purposes
        self.unusedWorkLoops = None

        # maps from canonical workloop name
        # to process id on the soapHost
        self.workLoopToPid = None

        self.fillWorkLoopData()

        # create an xmlrpc client
        import xmlrpclib

        self.rpcclient = xmlrpclib.ServerProxy("http://%s:%s" % (soapHost, launcherPort))

    #----------------------------------------

    def fillWorkLoopData(self):
        # this is called on init and must also be called
        # when the xdaq processes are restarted

        # if we are called the first time we don't do
        # consistency checks
        #
        # if this is called after restarting the xdaq processes
        # we insist that the work loops are equivalent
        # (apart from the actual process ids)
        isFirst = self.workerList is None

        # fetch the information about the workloops
        self.workerList = getWorkLoops((self.soapHost, self.soapPort))

        # canonicalize work loop names
        if isFirst:
            self.wlnToCanonical = canonicalizeWorkLoopNames(self.workerList.keys())
        else:
            assert self.wlnToCanonical == canonicalizeWorkLoopNames(self.workerList.keys())

        makeUnusedWorkLoops = lambda: sorted(
            [ wln 
              for wln in self.workerList.keys()
              if not wln in self.wlnToCanonical.keys()              
              ])
        
        if isFirst:
            self.unusedWorkLoops = makeUnusedWorkLoops()
        else:
            assert self.unusedWorkLoops == makeUnusedWorkLoops()


        # maps from canonical workloop name
        # to process id on the soapHost
        #
        # this will be different from the previous call
        # so no reason to compare to potentially existing data

        # print changes in workloop IDs after an EVB
        # restart (mainly for debugging)
        oldAssignments = self.workLoopToPid
        self.workLoopToPid = {}

        for wln, cwln in self.wlnToCanonical.items():
            
            self.workLoopToPid[cwln] = self.workerList[wln]['SYS_gettid']

            import logging
            if not isFirst:
                logging.debug("changing workloop %s from PID %d to %d" % (cwln, oldAssignments[cwln], self.workLoopToPid[cwln]))

    #----------------------------------------

    def getCanonicalWorkLoopNames(self):
        return self.workLoopToPid.keys()

    #----------------------------------------

    def pinThread(self, canonicalWorkLoopName, core):
        # pin the process to the given core
        pid = self.workLoopToPid[canonicalWorkLoopName]
        self.rpcclient.pinProcess(pid, core)

    #----------------------------------------

    def getCurrentThreadPinnings(self):
        """:return a dict of canonical work loop name to the CPU core number
        where the thread last ran"""

        result = {}

        if self.workLoopToPid is None:
            # not yet set
            return result

        # collect the list of all PIDs to look at
        pids = list(self.workLoopToPid.values())

        # pinnings will be a map of pid -> last CPU used
        # (note that the pids will be strings, not ints)
        lastCpus = self.rpcclient.getLastCpuOfProcesses(pids)

        # map back from pids to work loop names
        for wln, pid in self.workLoopToPid.items():
            result[wln] = lastCpus[str(pid)]

        return result


    #----------------------------------------

    def getCpuTicks(self):
        """
        :return: a nested dict:

        { "timestamp": ...,
          "cputicks": {
              a dict of canonical work loop name to a tuple (utime, stime)
              where utime and stime are the number of ticks the corresponding
              work loop was active (user and system time) as read for /proc/<pid>/stat
              }
        }
        """

        result = {}

        if self.workLoopToPid is None:
            # not yet set
            return result

        # collect the list of all PIDs to look at
        pids = list(self.workLoopToPid.values())

        # pinnings will be a map of pid -> last CPU used
        # (note that the pids will be strings, not ints)
        timestamp, tickData = self.rpcclient.getProcessesTicks(pids)

        # map back from pids to work loop names
        for wln, pid in self.workLoopToPid.items():
            result[wln] = tickData[str(pid)]

        return dict(timestamp = timestamp, cputicks = result)



def WorkLoopDataGetCpuTicksWrapper(workLoopData):
    """Wrapper around WorkLoopData.getCpuTicks() for multiprocessing"""
    return workLoopData.getCpuTicks()

#----------------------------------------------------------------------
