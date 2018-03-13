#!/usr/bin/env python

import logging, time

class DeapRunner:
    # class for configuring and running the genetic algorithm
    # for optimizing the work loop to core assignments

    def __init__(self, coreNumbers, goalFunction, resultFname = None):
        # configures the genetic algorithm toolbox
        # 
        # @param coreNumbers is the list of core numbers which can be
        # used to pin these threads to
        #
        # @param goalFunction must be an instance of GoalFunctionDeap

        # the function which pins the threads
        self.goalFunction = goalFunction

        #----------
        self.parameterNames = goalFunction.getParameterNames()

        # make an (ordered) copy of the core numbers
        self.coreNumbers = list(coreNumbers)

        import numpy
        import random
        from deap import algorithms

        from deap import base, tools, creator

        # we want to maximize the throughput (positive weight)
        creator.create("FitnessMax", base.Fitness, weights=(1.0,)) 

        # we use list of core values as 'individual' 
        # (which we then combine with the parameter names to 
        #  evaluate the point)
        creator.create("Individual", list, fitness = creator.FitnessMax)

        self.toolbox = base.Toolbox()

        self.toolbox.register("evaluate", self.evaluate)
        self.toolbox.register("mate", tools.cxTwoPoint)

        # define the mutation operator
        # self.toolbox.register("mutate", tools.mutFlipBit, indpb = 0.05)
        self.toolbox.register("mutate", self.changeCore, indpb = 0.05)

        self.toolbox.register("select", tools.selTournament, 
                              tournsize = 3 # number of individuals (solutions)
                                            # participating in each tournament
        )

        # defnine how to generate a parameter value:
        # randomly sample from the list of given core numbers
        self.toolbox.register("attr_core", lambda: random.choice(self.coreNumbers))

        # define what how many and what type of parameters
        # an individual is made of
        self.toolbox.register("individual", 
                              tools.initRepeat, 
                              creator.Individual,
                              self.toolbox.attr_core, 
                              len(self.parameterNames) # number of parameters per individual
                )

        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        # register our custom mapping function with some instrumentation to keep track
        # of generation and evaluation index within the generation
        self.toolbox.register("map", self.instrumentedMap)

        # open output file for writing
        if resultFname is not None:
            import csv

            headerNames = [ 'book_time', 
                             'generation',
                             'eval_index', # index of evaluation within the generation
                             'rate',
                             'rate_uncert',
                             ]
            
            # add parameter names
            headerNames += [ "args/" + paramName for paramName in self.parameterNames ]

            self.csvFile = open(resultFname, "w")
            self.csvWriter = csv.DictWriter(self.csvFile, headerNames)

            # does not exist on default csv version on CC7
            # self.csvWriter.writeheader()
            # in order to guarantee consistent ordering of the field
            # names we write them out as if they were data (see https://stackoverflow.com/a/13496970/288875)
            self.csvWriter.writerow(dict(zip(headerNames, headerNames)))
        else:
            self.csvWriter = None

    #----------------------------------------

    def changeCore(self, individual, indpb):
        # custom mutation operator:
        # for each of the elements in individual, 
        # changes the core number 
        # 
        # see e.g. also https://github.com/DEAP/deap/blob/232ed17142da1c8bb6a39179018f8278b122aada/deap/tools/mutation.py#L116

        import random

        for i in xrange(len(individual)):
            if not isinstance(individual[i], int):
                continue

            if random.random() >= indpb:
                continue

            # generate a new value but make sure
            # it is different from the current one
            # (this assumes that we have more than one
            # value to chose from and that we can find
            # a different value quite quickly

            while True:
                newValue = self.toolbox.attr_core()
                if newValue != individual[i]:
                    individual[i] = newValue
                    break

        return individual,

    #----------------------------------------

    def run(self):
        # run the evolutionary algorithm

        self.generation = 0
        self.evalIndex = None

        from deap import tools, algorithms

        # 60 individuals in the population at about 10 seconds evaluation
        # per individual will result in a new generation of solutions
        # every 600 seconds (10 minutes)
        pop = self.toolbox.population(n = 60)

        # best solution(s) found
        hof = tools.HallOfFame(10)

        self.population, self.log = algorithms.eaSimple(pop, self.toolbox, 
                                                        cxpb  = 0.5,         # crossing probability
                                                        mutpb = 0.2,         # mutation probability
                                                        ngen  = 100000000,   # (maximum) number of generations to run
                                                        # stats = stats, 
                                                        halloffame = hof, 
                                                        verbose = True)


    #----------------------------------------

    def evaluate(self, params):
        # wrapper function around the goal function, also doing
        # some generic work like writing out the parameters
        # and performance to a file for later analysis

        # @param params is a list of core numbers,
        # we combine it here with the list of parameter
        # names into a dict
        
        paramDict = dict(zip(self.parameterNames, params))

        now = time.time()

        # evaluate the goal function
        rateMean, rateStd, lastRate = self.goalFunction(paramDict)

        # append to the result .csv file
        if self.csvWriter is not None:
            # gmtime to be consistent with the hyperopt conversion
            values = dict(book_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(now)),
                          generation = self.generation,
                          eval_index = self.evalIndex,
                          rate = rateMean,
                          rate_uncert = rateStd
                          )
            # add parameter items
            for name, value in paramDict.items():
                values["args/" + name] = value

            self.csvWriter.writerow(values)
            self.csvFile.flush()

        if rateMean < 1 or lastRate < 1:
            logger = logging.getLogger("evaluate")

            # EVM seems to stay in ready state we must check
            # RU and BU states
            applicationStates = self.goalFunction.getApplicationStates()

            # count application states (we don't have collections.Counter
            # in python 2.6 on CC7)
            failedPerType = {}
            for appType, stateList in applicationStates.items():
                for state in stateList:
                    if state == 'Failed':
                        failedPerType[appType] = failedPerType.get(appType,0) + 1

            logger.warn("event rate almost zero (%.1f Hz) or last rate almost zero (%.1f Hz)" % (rateMean, lastRate))
            
            if failedPerType:
                logger.error("%d applications in failed state" % len(failedPerType))

                # must request a restart
                raise Exception("applications in failed state")
            else:
                logger.error("no applications in failed state")



        # it looks like this must return a tuple, hence the comma
        return rateMean,

    #----------------------------------------

    def instrumentedMap(self, func, items):

        # a map function which counts the generation number such
        # that we can keep track of the generation number
        # and the evaluation within the generation number

        logger = logging.getLogger("map")

        logger.info("----------")
        logger.info("map at generation %d" % self.generation)
        logger.info("----------")        

        # number of evaluation within this generation
        self.evalIndex = 0

        # perform the actual mapping
        result = []

        for item in items:
            result.append(func(item))
            self.evalIndex += 1

        # prepare next iteration
        self.generation += 1

        return result

#----------------------------------------------------------------------

