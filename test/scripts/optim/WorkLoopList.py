#!/usr/bin/env python

from WorkLoopData import WorkLoopData

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


