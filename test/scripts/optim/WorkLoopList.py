#!/usr/bin/env python

from WorkLoopData import WorkLoopData, WorkLoopDataGetCpuTicksWrapper

class WorkLoopList:
    # keeps information about all the relevant work loops to tune
    # on all hosts involved in a test

    #----------------------------------------

    def __init__(self, applications):
        # @param applications must be a dict of appType -> list of applications
        # where appType is typically 'RU', 'BU' or 'RUBU' (this is used
        # as a prefix for parameter names to make sure we have different
        # parameters to tune for the same work loop on different host types)
        #
        # the application data must be of the same format as the one 
        # used in Configuration.applications

        # maps from application type to list of parameters
        self.parameterNames = {}

        # maps from application type to list of WorkLoopData objects
        # (which can be used later to pin threads to different cores)
        self.workLoopDatas = {}

        # perform some checks:
        # - all applications of the same type must have the exact same
        #   list of workloops to tune

        # for the moment we insist that all RUs and all BUs have
        # the same list of worker loops (no hybrid system, e.g. with 
        # varying number of FEDs)
        # we tune all RUs and all BUs at the same way
        #
        # note that work loops contain ALL work loops so we have
        # to distinguish RU and BU workloops ourselves in some cases

        for appType, applicationList in applications.items():

            thisParameterNames = None

            # union of unused workloops for this application type
            unusedWorkLoops = set()

            self.workLoopDatas[appType] = []

            # retrieve work loop information from this application
            for application in applicationList:
                workLoopData = WorkLoopData(appType, 
                                            application['soapHostname'],
                                            int(application['soapPort']),
                                            application['launcherPort'])

                self.workLoopDatas[appType].append(workLoopData)

                unusedWorkLoops = unusedWorkLoops.union(workLoopData.unusedWorkLoops)
                
                if thisParameterNames is None:
                    thisParameterNames = sorted(workLoopData.getCanonicalWorkLoopNames())
                    self.parameterNames[appType] = thisParameterNames
                else:
                    assert thisParameterNames == sorted(workLoopData.getCanonicalWorkLoopNames()), "inconsistent canonical workloop names found for application type " + str(appType)

            # print warning of work loops not tuned
            if unusedWorkLoops:
                import logging
                logging.info("WARNING: not testing pinning of %d work loops for application type %s:" % (len(unusedWorkLoops), appType))
                for wln in sorted(unusedWorkLoops):
                    logging.info("  %s" % wln)

    #----------------------------------------
        
    def applyPinning(self, parameterValues):
        # @param parameterValues must be a map of parameter name -> core to pin this work loop to

        # TODO: this should be parallelized (over hosts and parameter names)
        
        # TODO: add a check if the full set of parameters were given
        for paramName, paramValue in parameterValues.items():
            appType, canonicalWorkLoopName = paramName.split('/',1)
            
            # change pinning for the given application type (RU, BU, RUBU)
            # and the canonical work loop name on all hosts
            for workLoopData in self.workLoopDatas[appType]:
                workLoopData.pinThread(canonicalWorkLoopName, paramValue)

    #----------------------------------------

    def getParameterNames(self):
        # returns a list of parameters to tune 
        # corresponding to the different workloops
        # of the different types of hosts

        result = []
        for appType, perAppParameters in self.parameterNames.items():
            for paramName in perAppParameters:

                # prefix the parameter names with the application type
                result.append(appType + "/" + paramName)

        return sorted(result)

    #----------------------------------------

    def fillWorkLoopData(self):
        # re-reads information about the workloops
        # this should be called after restarting the xdaq
        # processes

        for workLoopDataList in self.workLoopDatas.values():
            for workLoopData in workLoopDataList:
                workLoopData.fillWorkLoopData()

    #----------------------------------------

    def getCurrentThreadPinnings(self):
        """:return a nested dict with information about the work loop
        to cpu core assignments.
        The first index is the application type (e.g. RU),
        the second index is a tuple (soap host, soap port)
        the third index is the (canonical) work loop name
        the value is the cpu core this work loop was last found running on
        """
        result = {}

        for appType, workLoopDatas in self.workLoopDatas.items():

            thisResult = {}

            for workLoopData in workLoopDatas:
                key = (workLoopData.soapHost, workLoopData.soapPort)

                thisResult[key] = workLoopData.getCurrentThreadPinnings()

            result[appType] = thisResult

        return result

    #----------------------------------------

    def getCpuTicks(self, mpPool = None):
        """
        Method to collect CPU usage information across the entire setup for
        the monitored XDAQ workloops

        :param mpPool: if specified, this must be a multiprocessing pool which is
            used to collect the information from the different applications in parallel.
            Note that since the xmlrpc objects contained in this class are not
            pickleable, this will not work with a 'real' multiprocessing pool
            but only a (thread based) multiprocessing.dummy instance.

        :return: a nested dict:

        { "BU": {
           "workloop1": { (host, port): { "timestamp": ... "user_ticks": ... , "system_ticks" ... }
                          ...
                       }
            }
        }"""

        result = {}

        # concatenate the workLoopDatas into a flattened list so we could use
        # it with multiprocessing
        import operator
        wlds = reduce(operator.__add__, self.workLoopDatas.values())

        if not mpPool is None:
            # use a multithreading pool to collect the information
            # build a list
            results = mpPool.map(WorkLoopDataGetCpuTicksWrapper, wlds)
        else:
            # execute serially
            results = [ workLoopData.getCpuTicks() for workLoopData in wlds ]

        # put results into a dict
        for workLoopData, cpuData in zip(wlds, results):

            # key of thisAppTypeResult is work loop name
            thisAppTypeResult = result.setdefault(workLoopData.appType, {})

            timestamp = cpuData['timestamp']
            cpuTicks = cpuData['cputicks']

            key = (workLoopData.soapHost, workLoopData.soapPort)

            # group ticks by work loop name
            for workLoopName, data in cpuTicks.items():
                thisAppTypeResult.setdefault(workLoopName, {})[key] = dict(
                    timestamp = timestamp,
                    user_ticks = data[0],
                    system_ticks = data[1],
                )

            # end of loop over workLoopDatas

        return result
