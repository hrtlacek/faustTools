#!/usr/bin/env python

import argparse

parser = argparse.ArgumentParser(description='Watch a dsp file for changes and take a specific action.')
parser.add_argument('dspFile', metavar='N', type=str, 
                    help='Path to a .dsp file')
parser.add_argument('--svg', dest='svg', action='store_const',
                    const=True, default=False,
                    help='Make an svg block diagram and open it.')

parser.add_argument('--ir', dest='ir', action='store_const',
                    const=True, default=False,
                    help='Get impulse response and plot it.')
parser.add_argument('--af', dest='af', type=str,nargs=1, default='', help='Send through audio file.')

parser.add_argument('--line', dest='line', action='store_const',
                    const=True, default=False,
                    help='Get response to line from -1 to 1. So input-output amplitude relationship.')



# parser.add_argument('--plot', dest='plot', action='store_const',
#                     const=True, default=False,
#                     help='Plot output of faust program.')


args = parser.parse_args()
dspFile = args.dspFile
svg = args.svg
ir = args.ir
try:
    af = args.af[0]
except:
    af = ''
line = args.line

import pyinotify
import subprocess,shlex
import os
import numpy as np
from scipy.io import wavfile
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
plt.ion()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class DspFileHandler():
    def __init__(self, dspFile, svg=False, ir=False, af='', line=False):
        self.svg = svg
        self.dspFile = dspFile
        self.ir = ir
        self.af =af
        self.line=line
        self.dspDir = os.path.dirname(os.path.abspath(dspFile))
        print(self.dspDir)
        self.baseName = os.path.basename(dspFile)
        self.projectName = self.baseName[:-4]
        self.outputPath='/tmp/offlineOutput.wav'
        self.inputPath='/tmp/offlineInput.wav'
        self.sr = 44100

    def compute(self):
        if self.svg:
            cmd = 'faust --svg '+self.dspFile
            cmd = shlex.split(cmd)
            proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            resp = proc.communicate()[0]
            if 'ERROR' in resp:
                print bcolors.FAIL+'>[ER]'+bcolors.ENDC+resp
            elif 'WARNING' in resp:
                print bcolors.WARNING+'>[WA]'+bcolors.ENDC+resp
                self.openSVG()
            else:
                print bcolors.OKGREEN+'>[OK]'+bcolors.ENDC
                self.openSVG()
        if self.ir:
            returnCode = self.compile()
            if returnCode <2:
                self.getIR()
                self.plotSignal()
        if self.line:
            self.getLineResponse()
            self.plotSignal()
            
            # self.binaryPath = 'offlineProcessor'
            # outfileCpp = 'offline.cpp'
            # cmd = 'faust -a /opt/faudiostream-code/architecture/sndfile.cpp -o '+outfileCpp+' '+self.dspFile            
            # cmd = shlex.split(cmd)
            # proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # resp = proc.communicate()[0]

            # cmd = 'g++ -lsndfile '+outfileCpp+' -o '+self.binaryPath            
            # cmd = shlex.split(cmd)
            # proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # resp = proc.communicate()[0]
            # if 'ERROR' in resp:
            #     print bcolors.FAIL+'>[ER]'+bcolors.ENDC+resp
            # elif 'WARNING' in resp:
            #     print bcolors.WARNING+'>[WA]'+bcolors.ENDC+resp
            #     self.getIR()
            #     # self.openSVG()
            # else:
            #     print bcolors.OKGREEN+'>[OK]'+bcolors.ENDC
            #     # self.openSVG()
            #     self.getIR()
            #     self.plotSignal()
        if len(self.af)>0:
            self.binaryPath = 'offlineProcessor'
            outfileCpp = 'offline.cpp'
            cmd = 'faust -a /opt/faudiostream-code/architecture/sndfile.cpp -o '+outfileCpp+' '+self.dspFile            
            cmd = shlex.split(cmd)
            proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            resp = proc.communicate()[0]

            cmd = 'g++ -lsndfile '+outfileCpp+' -o '+self.binaryPath            
            cmd = shlex.split(cmd)
            proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            resp = proc.communicate()[0]
            if 'ERROR' in resp:
                print bcolors.FAIL+'>[ER]'+bcolors.ENDC+resp
            elif 'WARNING' in resp:
                print bcolors.WARNING+'>[WA]'+bcolors.ENDC+resp
                self.processFile(self.af)
                self.sr, self.inputSignal = wavfile.read(self.af)
                # self.openSVG()
            else:
                print bcolors.OKGREEN+'>[OK]'+bcolors.ENDC
                # self.openSVG()
                self.processFile(self.af)
                self.sr, self.inputSignal = wavfile.read(self.af)
                self.plotSignal()
        return

    def compile(self):
        self.binaryPath = 'offlineProcessor'
        outfileCpp = 'offline.cpp'
        cmd = 'faust -a /opt/faudiostream-code/architecture/sndfile.cpp -o '+outfileCpp+' '+self.dspFile            
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        resp = proc.communicate()[0]

        cmd = 'g++ -lsndfile '+outfileCpp+' -o '+self.binaryPath            
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        resp1 = proc.communicate()[0]

        if 'ERROR' in resp:
            print bcolors.FAIL+'>[ER]'+bcolors.ENDC+resp
            return 2
        elif 'WARNING' in resp:
            print bcolors.WARNING+'>[WA]'+bcolors.ENDC+resp
            return 1
            # self.processFile(self.af)
            # self.sr, self.inputSignal = wavfile.read(self.af)
            # self.openSVG()
        else:
            print bcolors.OKGREEN+'>[OK]'+bcolors.ENDC
            # self.openSVG()
            return 0
            # self.processFile(self.af)
            # self.sr, self.inputSignal = wavfile.read(self.af)
            # self.plotSignal()

        # return

    def openSVG(self):
        
        svgPath = os.path.join(self.dspDir,self.projectName+'-svg','process.svg')
        cmd = 'xdg-open '+svgPath
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # resp = proc.communicate()

    def getIR(self):
        # tempPath = '/tmp/impulse.wav'
        # self.irPath = '/tmp/ir.wav'
        # sr = 44100
        lenSec = 0.5
        impOffsetSamps = 5000
        impLength = 10000
        imp = np.zeros(int(round(lenSec*self.sr)))
        imp[impOffsetSamps:impOffsetSamps+impLength] = 1
        self.processArray(imp)
        # self.inputSignal = imp
        # wavfile.write(tempPath, sr, imp)

        # cmd = os.path.join(self.dspDir,self.binaryPath)+' '+tempPath+' '+self.irPath            
        # cmd = shlex.split(cmd)
        # proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # resp = proc.communicate()[0]

        return

    def getLineResponse(self):
        line = np.linspace(-1,1,self.sr)
        self.processArray(line)
        return

    def processFile(self, tempPath):
        # tempPath = '/tmp/impulse.wav'
        # self.irPath = '/tmp/ir.wav'

        cmd = os.path.join(self.dspDir,self.binaryPath)+' '+tempPath+' '+self.outputPath            
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        resp = proc.communicate()[0]

        return
    
    def processArray(self,anArray, sr=44100,inputPath='/tmp/offlineInput.wav'):
        self.inputSignal = anArray
        wavfile.write(inputPath, sr, anArray)
        self.inputPath = inputPath
        
        cmd = os.path.join(self.dspDir,self.binaryPath)+' '+inputPath+' '+self.outputPath            
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        resp = proc.communicate()[0]
        return

    def plotSignal(self):
        fig = plt.gcf()
        plt.clf()
        sr,y = wavfile.read(self.outputPath)
        n = range(len(y))
        x = self.inputSignal
        plt.plot(n,y,n,x)
        plt.grid()
        plt.show()
        plt.pause(0.0001)
        

global MyDspHandler
MyDspHandler = DspFileHandler(dspFile,svg=svg, ir=ir, af=af, line=line)

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print "Creating:", event.pathname

    def process_IN_DELETE(self, event):
        print "Removing:", event.pathname

    def process_IN_CLOSE_WRITE(self,event):
        # print 'modified.'
        MyDspHandler.compute()


# Instanciate a new WatchManager (will be used to store watches).
wm = pyinotify.WatchManager()
# Associate this WatchManager with a Notifier (will be used to report and
# process events).
handler = EventHandler()
notifier = pyinotify.Notifier(wm,handler)
# Add a new watch on /tmp for ALL_EVENTS.
wm.add_watch(dspFile, pyinotify.ALL_EVENTS)
# Loop forever and handle events.
notifier.loop()

