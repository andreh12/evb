#!/usr/bin/env python


from argparse import ArgumentParser

# scans pinning of xdaq threads 'passively', i.e. attaches
# to an existing running setup (without starting one for the moment)

#----------------------------------------------------------------------
import os, sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))

from runBenchmarks import RunBenchmarks
from runScans import RunScans

import time, logging, re, os, sys, threading

import optimutils

from RestartableRunner import RestartableRunner
from RestartableRunnerRunScans import RestartableRunnerRunScans
from RestartableRunnerRunBenchmarks import RestartableRunnerRunBenchmarks

#----------------------------------------------------------------------
# main
#----------------------------------------------------------------------
if __name__ == "__main__":

    parser = ArgumentParser()

    subparsers = parser.add_subparsers(help ='subcommands to get the configuration. Run any of these with -h afterwards to get subcommands specific options help',
                                       dest = 'subcommand')

    #----------
    # getting the configuration using RunBenchmarks
    #----------
    runBenchmarksParser = subparsers.add_parser("runbenchmarks")

    runBenchmarks = RunBenchmarks()

    # add options to run the event builder
    runBenchmarks.addOptions(runBenchmarksParser)

    #----------
    # getting the configuration using RunScans
    #----------
    runScansParser = subparsers.add_parser("runscans")

    runScans = RunScans()

    # add options to run the event builder
    runScans.addOptions(runScansParser)

    #----------
    # parse the command line options 
    #----------
    options = parser.parse_args()

    # check which subcommand was specified


    if options.subcommand == 'runbenchmarks':
        testRunner = runBenchmarks
        testRunner.args = vars(options)
        testRunner.createSymbolMap()

        #----------
        # check/override some event builder options
        options.nbMeasurements = 0

        if len(options.sizes) != 1:
            print >> sys.stderr,"must specify excatly one superfragment size to run with (in the future we may support optimizing for a mix of fragment sizes)"
            sys.exit(1)
    elif options.subcommand == 'runscans':
        testRunner = runScans
        testRunner.args = vars(options)

    else:
        raise Exception("internal error, uncaught case")


    #----------

    if not os.path.exists(options.outputDir):
        os.makedirs(options.outputDir)

    timeStamp = optimutils.initLogging(os.path.join(options.outputDir, "evb-pinning-deap-{timestamp}.log"), timestamp = None)
    logging.info("startup of optimization")

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

    #----------
    # the object to launch the event builder processes
    # and restart them on failure
    if options.subcommand == 'runbenchmarks':
        evbRunner = RestartableRunnerRunBenchmarks(testRunner)
    elif options.subcommand == 'runscans':
        evbRunner = RestartableRunnerRunScans(testRunner)
    else:
        raise Exception("internal error, uncaught case")
    #----------

    #----------
    # launch the event builder 
    # so that we can read the list of workloops and
    # decide which ones to tune
    #----------

    devnull = open("/dev/null", "w")

    evbRunnerThread = threading.Thread(target = evbRunner.run,
                                       args = (devnull,))
    logging.info("starting EVB")
    evbRunnerThread.start()

    # wait for the EVB to finish starting
    logging.info("waiting for completion of EVB start")
    evbRunner.evbStarted.wait()
    logging.info("EVB start complete")

    # now we can get the benchmark configuration
    logging.info("getting configuration")
    config = testRunner.getAllConfigurations()[0]['config']

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
    goalFunction = GoalFunctionDeap(config, workLoopList)

    # write the event rate before tuning
    time.sleep(1)
    rateMean, rateStd, lastRate = goalFunction.getEventRate()
    logging.info("readout rate before tuning: %.1f +/- %.1f kHz" % (rateMean / 1e3, rateStd / 1e3))
    logging.info("starting scan")

    # run optimization 
    from DeapRunner import DeapRunner
    runner = DeapRunner(cpuList, goalFunction,
                        resultFname = os.path.join(options.outputDir, "evb-pinning-deap-{timestamp}.csv").format(timestamp = timeStamp),
                        evbRunner = evbRunner
                   )

    try:
        runner.run()
    except Exception, ex:
        logging.warn("got exception: " + str(ex))

    finally:
        # this also catches KeyboardInterrupt (CTRL-C)
        evbRunner.stopEVB()
        evbRunnerThread.join()
        


