#!/usr/bin/env python

import argparse
import glob
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import SocketServer

from SimpleXMLRPCServer import SimpleXMLRPCServer

class ExitableServer(SimpleXMLRPCServer):
    # an XMLRPC server which can exit

    def serve_forever(self):
        self.stop = False
        while not self.stop:
            self.handle_request()

class xdaqThread(threading.Thread):

    def __init__(self,xdaqPort,logFile,useNuma, logLevel, dummyXdaq):
        threading.Thread.__init__(self)
        self.logFile = logFile
        self._process = None
        self.logLevel = logLevel

        # if True, start the dummy xdaq script instead of xdaq.exe
        self.dummyXdaq = dummyXdaq

        xdaqRoot = os.environ["XDAQ_ROOT"]
        os.environ["XDAQ_DOCUMENT_ROOT"] = xdaqRoot+"/htdocs"
        os.environ["LD_LIBRARY_PATH"] = xdaqRoot+"/lib"
        hostname = socket.gethostname()
        numaCtl = []
        if useNuma:
            if 'ru-' in hostname:
                numaCtl = ['/usr/bin/numactl','--cpunodebind=1','--membind=1']
            elif 'bu-' in hostname:
                numaCtl = ['/usr/bin/numactl','--physcpubind=10,12,14,26,28,30','--membind=1']
            elif 'dvrubu-' in hostname:
                numaCtl = ['/usr/bin/numactl','--cpunodebind=0','--membind=0']

        if self.dummyXdaq:
            # launch dummyXdaq.py (during development)

            # get the absolute directory of the file where this code is in
            dummy_xdaq_path = os.path.abspath(os.path.dirname(__file__))

            self._xdaqCommand = [ "/usr/bin/python",
                                  os.path.join(dummy_xdaq_path, "dummyXdaq.py"),
                                  "-p" + str(xdaqPort)
                                  ]
        else:
            # launch the real xdaq.exe
            self._xdaqCommand = numaCtl + [xdaqRoot+"/bin/xdaq.exe","-e"+xdaqRoot+"/etc/default.profile","-p"+str(xdaqPort)]


    def run(self):

        command = list(self._xdaqCommand)
        if self.logLevel is not None:
            command.append("-l" + self.logLevel)

        if self.logFile:
            with open(self.logFile,"w",0) as logfile:
                self._process = subprocess.Popen(command,stdout=logfile,stderr=subprocess.STDOUT,close_fds=True)
        else:
            self._process = subprocess.Popen(command)
        self._process.wait()


    def kill(self):
        if self._process:
            self._process.kill()


class xdaqLauncher:

    threads = {}

    def __init__(self, logDir, useNuma, dummyXdaq):

        self.xmlrpcServer = None

        self.logDir = logDir
        self.useNuma = useNuma

        # log level to be used for the XDAQ process
        self.logLevel = None

        # if True, use dummyXdaq.py instead of xdaq.exe
        self.dummyXdaq = dummyXdaq

        # /dev/null to redirect subcommand output
        self.devnull = open(os.devnull, "w")

        # remove core files in /tmp on startup
        for fname in glob.glob("/tmp/core.*"):
            try:
                os.remove(fname)
            except OSError:
                pass

    def cleanTempFiles(self):
        try:
            for file in glob.glob("/tmp/dump_*txt"):
                os.remove(file)
            shutil.rmtree("/tmp/evb_test")
        except OSError:
            pass


    def getLogFile(self,testname):
        if self.logDir:
            return self.logDir+"/"+testname+"-"+socket.gethostname()+".log"
        else:
            return None


    def startXDAQ(self,port,testname):

        if self.logDir and testname is None:
            raise Exception("Please specify a testname")
        if port is None:
            raise Exception("Please specify a port number")
        if port in xdaqLauncher.threads and xdaqLauncher.threads[port].is_alive():
            raise Exception("There is already a XDAQ process running on port "+str(port))
        self.cleanTempFiles()
        try:
            thread = xdaqThread(port,self.getLogFile(testname),self.useNuma, self.logLevel, self.dummyXdaq)
            thread.start()
        except KeyError:
            raise Exception("Please specify XDAQ_ROOT")
        xdaqLauncher.threads[port] = thread
        return "Started XDAQ on port "+str(port)


    def killProcess(self,port):
        thread = xdaqLauncher.threads[port]
        if thread.is_alive():
            thread.kill()
            thread.join()
            return "Killed XDAQ process on port "+str(port)
        elif thread._process:
            return "XDAQ process on port "+str(port)+" has already died: "+str(thread._process.returncode)
        else:
            return "XDAQ process on port "+str(port)+" does not exist"


    def stopXDAQ(self,port):
        response = ""
        self.cleanTempFiles()
        if port is None:
            for port in xdaqLauncher.threads.keys():
                response += self.killProcess(port)+"\n"
        else:
            try:
                response = self.killProcess(port)
            except KeyError:
                raise Exception("There is no XDAQ processes on port "+str(port))
        if response == "":
            return "There are no running XDAQ processes"
        else:
            return response


    def stopLauncher(self):
        response = ""
        for port in xdaqLauncher.threads.keys():
            response += self.killProcess(port)+"\n"
        response += "Terminating launcher"

        # tell the XML rpc server to stop serving requests
        if not self.xmlrpcServer is None:
            self.xmlrpcServer.stop = True

        return response


    def getFiles(self,port,dir):
        if dir is None:
            raise Exception("Please specify a directory")
        return str(os.listdir(dir))


    def getNumaInfo(self):
        if 'dvrubu-c2e34' in socket.gethostname():
            numaInfo = {'ibvCPU':'0','ethCPU':'1'}
        elif 'dvrubu-' in socket.gethostname():
            numaInfo = {'ibvCPU':'1','ethCPU':'0'}
        else:
            numaInfo = {'ibvCPU':'0','ethCPU':'1'}
        numactl = subprocess.check_output(['numactl','--hardware'])
        for m in re.finditer('node ([0-9]+) cpus: ([0-9 ]+)',numactl):
            numaInfo[m.group(1)] = m.group(2).split()
        return numaInfo


    def setLogLevel(self, level):
        # sets the XDAQ log level for the given application
        # this must be called before starting the XDAQ process in question
        self.logLevel = level


    def pinProcess(self, pid, core):
        # pins the process pid to the given core

        mask = hex(1 << core)
        status = subprocess.call(["/bin/taskset", "-p", mask, str(pid)], stdout = self.devnull)

        return status

    def __parseProcPidStat(self, data):
        """Given a line read from /proc/<pid>/stat, returns
        a list of entries. Note that this does NOT read
        any such file (such e.g. the reading of multiple
        files can be done at once and the parsing later such
        that the status information read for multple PIDs
        is closer in time)

        :param data the first line of the corresponding /proc/<pid>/stat file
        to be parsed
        :return a list of the elements found or None if an unexpected
        format was encountered
        """

        #              pid     executable
        # we assume that there is no parenthesis in the executable name
        mo = re.match("(\d+) \((.+)\) ", data)

        if not mo:
            # there is an unexpected format, silently ignore it for the moment
            return None

        rest = data[mo.end():].lstrip()

        # rest contains values from position 3 on (as described
        # in the above man page), i.e. the index in parts
        # is the index in the man page minus 3.
        return [ mo.group(1), mo.group(2)] + re.split('\s+', rest)


    def getLastCpuOfProcesses(self, processes):
        """Given a list of thread (process) ids, returns the
        last cpu used according to /proc/<pid>/stat .

        :param processes a list of thread ids (integers) for which
               the last used CPU should be returned.

        :return a dict of thread id to last cpu used. Note that they
                keys will be strings, not integers (as required
                by python xmlrpc)
        """

        result = {}

        for pid in processes:
            # see e.g. http://man7.org/linux/man-pages/man5/proc.5.html
            # for the format of /proc/<pid>/stat

            with open("/proc/%s/stat" % pid) as fin:
                parts = self.__parseProcPidStat(fin.readline())

                if parts is None:
                     continue

                # numbers in the above proc man page start at one so we subtract one
                proc = int(parts[39 - 1])

                # convert pid to a string, see https://stackoverflow.com/questions/6996585
                result[str(pid)] = proc

        return result



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-l","--logDir",help="redirect stdout and stderr to log file")
    parser.add_argument("-n","--useNuma",action='store_true',help="use numactl to start xdaq.exe")
    parser.add_argument("--dummyXdaq",default = False, action='store_true', help="run dummyXdaq.py instead of xdaq.exe (useful for development)")
    parser.add_argument("port",type=int)
    args = vars( parser.parse_args() )
    hostname = socket.gethostbyaddr(socket.gethostname())[0]
    if args['useNuma'] and any(x in hostname for x in ('ru-','bu-')):
        useNuma = True
    else:
        useNuma = False

    server = ExitableServer((hostname,args['port']),
                            bind_and_activate = False,
                            logRequests = False)
    server.allow_reuse_address = True
    try:
        server.server_bind()
    except socket.error, ex:
        import errno
        if ex.errno == errno.EADDRINUSE:
            raise Exception("xdaq launcher address already in use on %s:%s" % (hostname, args['port']))
        else:
            raise

    server.server_activate()

    launcher = xdaqLauncher(logDir = args['logDir'], useNuma = useNuma, dummyXdaq = args['dummyXdaq'])

    # add the server to the xdaqLauncher object
    # so that it can set the stop flag
    launcher.xmlrpcServer = server

    # for the moment we prefer to register methods individually
    # rather than calling register_instance() which registers
    # all methods of xdaqLauncher

    for command in [ "startXDAQ",
                     "stopXDAQ",
                     "stopLauncher",
                     "getFiles",
                     "getNumaInfo",
                     "setLogLevel",
                     "pinProcess",
                     "getLastCpuOfProcesses",
                     ]:
        server.register_function(getattr(launcher, command))

    # start serving requests
    server.serve_forever()
