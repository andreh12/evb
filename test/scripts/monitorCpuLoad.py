#!/usr/bin/env python

import os, requests, re, time

from SymbolMap import SymbolMap
from messengers import sendSoapMessage, SOAPexception, webPing

import numpy as np

#----------------------------------------------------------------------


class WorkLoopMonitor:
    """
    Class to repeatedly monitor the CPU usages of the workloops
    of the XDAQ applications given to it
    """

    def __init__(self, soapHostPorts):
        """
        :param soapHostPorts: list of (soapHost, soapPort) of the xdaq applications to monitor
        """

        # make a copy
        self._soapHostPorts = list(soapHostPorts)

        self._numApplications = len(self._soapHostPorts)

        self._pool = mp.Pool(20, init_worker)

        # contact all xdaq applications to find the mapping
        # of workloop name to thread (process) id

        # list of (lid, instance) of the ptv::ibv applications
        self._ibvLidsInstances = self._pool.map(getIbvLidsInstancesFromHyperdaq, hostPorts)

        # pre-pack arguments for when we run updates
        self._getterArgs = zip(self._soapHostPorts, [ item[0] for item in self._ibvLidsInstances])

        # keep track of the times of the last updates
        self._updateTimes = np.zeros(self._numApplications, dtype = 'float64')

        self._isFirstUpdate = True

        # keep track of times (in seconds) between updates
        # this can be useful for monitoring the number of total
        # read attempts
        self._deltaTimes = np.zeros(self._numApplications, dtype = 'float64')

        self._idleReceiveCounts = np.zeros(self._numApplications, dtype ='int64')

        self._successfulReceiveCounts = np.zeros(self._numApplications, dtype ='int64')

        # ratio of successful to (successful + idle) since last update
        self._successfulReceiveFraction = np.zeros(self._numApplications, dtype = 'float64')


    def update(self):
        """
        fetches the IBV counters from all applications
        """

        result = self._pool.map(getIbvCountersWrapper, self._getterArgs)

        # make copies (otherwise we modify the same arrays during the update)
        prevTimes = np.array(self._updateTimes)
        oldSuccesfulReceiveCounts = np.array(self._successfulReceiveCounts)
        oldIdleReceiveCounts = np.array(self._idleReceiveCounts)

        self._updateTimes = np.zeros(self._numApplications, dtype = 'float64')

        for i in range(self._numApplications):
            self._updateTimes[i] = result[i][0]
            self._idleReceiveCounts[i] = result[i][1]
            self._successfulReceiveCounts[i] = result[i][2]

        # update derived quantities

        if self._isFirstUpdate:
            self._isFirstUpdate = False
        else:
            # this is not the first update, we can calculate differences
            self._deltaTimes = self._updateTimes - prevTimes

            succesfullReceives = self._successfulReceiveCounts - oldSuccesfulReceiveCounts
            idleReceives = self._idleReceiveCounts - oldIdleReceiveCounts

            self._successfulReceiveFraction = succesfullReceives / (
                    succesfullReceives + idleReceives
            ).astype('float64')

#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    try:
        symbolMapfile = os.environ["EVB_TESTER_HOME"] + '/cases/' + os.environ["EVB_SYMBOL_MAP"]
        parser.add_argument("-m", "--symbolMap", default=symbolMapfile,
                            help="symbolMap file to use, [default: %(default)s]")
    except KeyError:
        parser.add_argument("-m", "--symbolMap", required=True, help="symbolMap file to use")

    args = parser.parse_args()


    symbolMap = SymbolMap(args.symbolMap)

    # get a list of all xdaq applications defined in the SymbolMap
    # (note that not all need to be existing when running)


    # build a dict to be used with WorkLoopList
    # SymbolMap.getHostInfo() produces dicts which
    # can be used with WorkLoopList but they
    # need to be grouped by host type

    applications = {}

    # shortHostType is e.g. 'BU' etc. (but not 'RUBU')
    for shortHostType in symbolMap.getShortHostTypes():

        for hostType in symbolMap.getHostsOfType(shortHostType):

            # this is the EVM, change the short host type for this host only
            if hostType == 'RU0':
                thisShortHostType = 'EVM'
            else:
                thisShortHostType = shortHostType

            # check which hosts of the SymbolMap are actually reachable
            hostInfo = symbolMap.getHostInfo(hostType)

            if not webPing(hostInfo['soapHostname'], hostInfo['soapPort']):
                # application not used in this test
                continue

            applications.setdefault(thisShortHostType, []).append(hostInfo)



    # for each host, get the list of XDAQ work loops
    from optim.WorkLoopList import WorkLoopList

    workLoopList = WorkLoopList(applications)

    # number of ticks per second at 100% CPU usage
    # the was taken from sysconf(_SC_CLK_TCK)
    # or with
    #    getconf CLK_TCK
    # on a shell
    hz = 100.

    prevCpuTickData = None

    # important: initialize the multiprocessing threadpool
    # as late as possible, everything cloned in the threads
    # must be exist already
    import multiprocessing.dummy as mp
    from TestCase import init_worker

    pool = mp.Pool(20, # init_worker
                   )

    while True:
        # retrieve information
        cpuTickData = workLoopList.getCpuTicks(
            # mpPool=pool
            )

        if not prevCpuTickData is None:
            # calculate differences with respect to previous iteration

            print "----------"
            print "per workloop CPU load"
            print "----------"

            for appType in sorted(cpuTickData.keys()):

                # appType is RU or BU
                print "%s (%d hosts, %d workloops):" % (appType, numHostsPerType[appType], len(cpuTickData[appType]))

                print "  %-40s: %5s   %5s   %5s" % ("work loop", "min", "avg", "max")

                for workLoopName in sorted(cpuTickData[appType].keys()):

                    # this is a dict of (soapHost, soapPort) -> dict with tick information and timestamp
                    wlData = cpuTickData[appType][workLoopName]

                    # this is a list of cpu loads (already converted from tick differences)
                    # over the different remote applications
                    cpuLoads = np.zeros(len(wlData), dtype = 'float32')

                    # find differences with respect to previous update
                    # and then calculate some summary statistics like
                    # min, max, mean, stddev etc.

                    for hostIndex, hostPort in enumerate(sorted(wlData.keys())):

                        # this is a dict with timestamp and cpu ticks information
                        hostData = wlData[hostPort]

                        prevHostData = prevCpuTickData[appType][workLoopName][hostPort]

                        deltaT = hostData['timestamp'] - prevHostData['timestamp']

                        # for the moment we just display the sum of user + system time
                        deltaTicks = hostData['user_ticks'] + hostData['system_ticks'] - \
                            prevHostData['user_ticks'] - prevHostData['system_ticks']


                        cpuLoads[hostIndex] = deltaTicks / float(deltaT)


                    cpuLoads *= 100. / hz

                    print "  %-40s: %5.1f%%  %5.1f%%  %5.1f%%" % (workLoopName, cpuLoads.min(), cpuLoads.mean(), cpuLoads.max())

                print

        else:
            # this is the first iteration

            # count the number of hosts of a given type, assume all have the same
            # set of workloops so just count the number of hosts on the first
            # workloop
            numHostsPerType = {}

            for appType, perAppTypeData in cpuTickData.items():
                # get the first (any) entry
                wlData = perAppTypeData.itervalues().next()
                numHostsPerType[appType] = len(wlData)

        # prepare the next iteration
        prevCpuTickData = cpuTickData

        time.sleep(1)

