import subprocess
import shlex
import sys
import os
import logging 

import zmq
import time
import pickle
import numpy as np
import config

# logging.basicConfig(level=logging.DEBUG)

class Plotter(object):
    def __init__(self, *args, randomizePort=True, port=5555):
        if randomizePort:
            self.port = np.random.randint(1000, 5000)
        else:
            self.port = port
        logging.debug('initializing plotter at port %i'%self.port)

        modDir = os.path.dirname(os.path.abspath(__file__))

        self.plotterFile = os.path.join(modDir, '_plotter_faustwatch.py')

        self.__createPlotProcess()  # create the plotting server/subprocess
        time.sleep(0.1)  # give the process some time to launch
        self.__connect()  # connect to the plotting server

        return

    def __connect(self):
        self.context = zmq.Context()
        return

    def __createPlotProcess(self):
        cmd = '/root/miniconda2/envs/findRefrain3/bin/python ' + \
            self.plotterFile+' '+str(self.port)
        logging.debug('starting subprocess via: '+ cmd)
        cmd = shlex.split(cmd)
        self.proc = subprocess.Popen(cmd)
        return

    def plot(self, arr):
        self.data = arr
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://127.0.0.1:"+str(self.port))

        pickled = pickle.dumps(self.data, protocol=0).decode('latin-1')
        msg = {'type': 'data', 'data': pickled}
        self.socket.send_json(msg)
        return

    def addPlot(self):
        return

    def destroy(self):
        self.proc.kill()
        return
