#!/usr/bin/env python

import argparse
import glob
import os
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

    def setLogLevel(self, level):
        # sets the XDAQ log level for the given application
        # this must be called before starting the XDAQ process in question
        self.logLevel = level

    def pinProcess(self, pid, core):
        # pins the process pid to the given core

        mask = hex(1 << core)
        status = subprocess.call(["/bin/taskset", "-p", mask, str(pid)])

        return status


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
    server.server_bind()
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
                     "setLogLevel",
                     "pinProcess",
                     ]:
        server.register_function(getattr(launcher, command))

    # start serving requests
    server.serve_forever()
