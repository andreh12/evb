#!/usr/bin/env python

# scans pinning of xdaq threads 'passively', i.e. attaches
# to an existing running setup (without starting one for the moment)

#----------------------------------------------------------------------
import os, sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))

import time, logging, re
from pprint import pprint
import numpy as np
import math
import os
import getpass

from optimutils import *

#----------------------------------------------------------------------

import sys, time
import logging

import numpy as np

#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------
if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()


    parser.add_argument("configFile", 
                        metavar = "config",
                        help="path to the configuration file which is run by runScans.py (this is used to find the RUs and BUs to tune)")

    parser.add_argument("-o","--outputDir",
                        metavar = "dir",
                        default = "/globalscratch/%s/scans" % getpass.getuser(),
                        help = "output directory where log file and results in .csv format will be written to [default: %(default)s]")

    options = parser.parse_args()

    # remove any trailing slash
    while options.configFile.endswith('/'):
        options.configFile = options.configFile[:-1]

    configName = os.path.splitext(os.path.basename(options.configFile))[0]
    if os.path.isdir(options.configFile):
        options.configFile += "/"+configName+".xml"

    # take the symbol map from the directory in which the configuration file resides
    symbolMapFname = os.path.join(os.path.dirname(options.configFile), "symbolMap.txt")
    from SymbolMap import SymbolMap
    symbolMap = SymbolMap(symbolMapFname)

    from Configuration import ConfigFromFile
    config = ConfigFromFile(symbolMap,options.configFile,
                            # dummy arguments
                            fixPorts = False,
                            useNuma = False,
                            generateAtRU = False,
                            dropAtRU = False,
                            dropAtSocket = False,
                            ferolMode = False
                            )

    #----------

    # on the RUBU:
    # CPU0 (Infiniband side):
    #   first physical cores: 0,2,4,..,14
    #   hyperthreads cores:   +16

    # CPU0 (Ethernet side):
    #   first physical cores: 1,3,5,..,15
    #   hyperthreads cores:   +16

    # list of cores to assign threads to
    # includes hyperthreads
    cpuList = range(32)


    if not os.path.exists(options.outputDir):
        os.makedirs(options.outputDir)

    timeStamp = initLogging(os.path.join(options.outputDir, "evb-pinning-deap-{timestamp}.log"), timestamp = None)

    logging.info("using configuration file " + os.path.abspath(options.configFile))

    #----------
    # find RUs, BUs and RUBUs
    # 
    # we group the workloops with equivalent names together for the same type of host (RU, BU)
    # note that some workloops have the same name on RUs and BUs but should be tuned
    # differently unless they are on RUBUs where they are shared between the RU and BU application
    #
    # currently we support RU+BU and RUBU setups but no mixing between RU,BU and RUBUs
    #----------
    rubus = config.getRUBUs()
    rus = config.applications['RU']
    bus = config.applications['BU']

    # we should remove RUBUs from list of RUs and BUs
    # (because RUBUs will also appear in the list of RUs and BUs)
    # for the moment, if we have RUBUs, we just look at them and
    # ignore the individual RUs and BUs assuming they are all contained
    # in the RUBUs

    from WorkLoopList import WorkLoopList

    if rubus:
        # we have at least one RUBU, assume all are RUBUs
        workLoopList = WorkLoopList(dict(RUBU = rubus))
        logging.info("setup with %d RUBUs" % len(rubus))
    else:
        workLoopList = WorkLoopList(dict(
                RU = rus,
                BU = bus))
        logging.info("setup with %d RUs and %d BUs" % (len(rus), len(bus)))


    logging.info("found %d work loops to tune" % len(workLoopList.getParameterNames()))

    #----------

    from GoalFunctionDeap import GoalFunctionDeap
    goalFunction = GoalFunctionDeap(config.applications, workLoopList)

    # write the event rate before tuning
    time.sleep(1)
    rateMean, rateStd, lastRate = goalFunction.getEventRate()
    logging.info("readout rate before tuning: %.1f +/- %.1f kHz" % (rateMean / 1e3, rateStd / 1e3))
    logging.info("starting scan")

    # run optimization 
    from DeapRunner import DeapRunner
    runner = DeapRunner(cpuList, goalFunction,
                        resultFname = os.path.join(options.outputDir, "evb-pinning-deap-{timestamp}.csv").format(timestamp = timeStamp)
                   )

    runner.run()
