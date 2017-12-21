#!/usr/bin/env python

#!/usr/bin/env python
#title           : faustwatch.py
#description     : utilities for FAUST development
#author          : Patrik Lechner <ptrk.lechner@gmail.com>
#date            : Nov 2017
#version         : 0.2
#usage           :
#notes           :
#python_version  : 2.7.13
#=======================================================================
from __future__ import print_function
__author__ = "Patrik Lechner <ptrk.lechner@gmail.com>"

import pyinotify
import subprocess,shlex
import os
import numpy as np
from scipy.io import wavfile
import matplotlib
import config
import scipy.signal as sig
matplotlib.use("TKAgg")
import matplotlib.pyplot as plt
# plt.ion()



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

parser.add_argument('--impLen', type=int, default = 1, help='Length of impulse. Default is unit impulse, so 1.')

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
impLen = args.impLen
try:
    af = args.af[0]
except:
    af = ''
line = args.line


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
    def __init__(self, dspFile, svg=False, ir=False, af='', line=False, impLen=1):
        self.svg = svg
        self.dspFile = dspFile
        self.ir = ir
        self.af =af
        self.line=line
        self.impLen = impLen

        self.dspDir = os.path.dirname(os.path.abspath(dspFile))
        print(self.dspDir)
        self.baseName = os.path.basename(dspFile)
        self.projectName = self.baseName[:-4]
        self.outputPath= config.audioOutPath 
        self.inputPath= config.audioInPath
        self.sr = 44100

    def compute(self):
        if self.svg:
            cmd = 'faust --svg '+self.dspFile
            cmd = shlex.split(cmd)
            proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            resp = proc.communicate()[0]
            if 'ERROR' in resp:
                print (bcolors.FAIL+'>[ER]'+bcolors.ENDC+resp)
            elif 'WARNING' in resp:
                print (bcolors.WARNING+'>[WA]'+bcolors.ENDC+resp)
                self.openSVG()
            else:
                print(resp)
                print (bcolors.OKGREEN+'>[OK]'+bcolors.ENDC)
                self.openSVG()
        if self.ir:
            returnCode = self.compile()
            if returnCode <2:
                self.getIR()
                self.plotSignal()
        if self.line:
            returnCode = self.compile()
            if returnCode <2:
                self.getLineResponse()
                self.plotSignal()

        if len(self.af)>0:
            returnCode = self.compile()
            if returnCode<2:
                self.inputPath = self.af
                self.sr, self.inputSignal = wavfile.read(self.af)
                self.processFile(self.af)
                self.plotSignal()

        return

    def compile(self):
        self.binaryPath = 'offlineProcessor'
        outfileCpp = 'offline.cpp'
        cmd = 'faust -a '+config.offlineCompArch+' -o '+outfileCpp+' '+self.dspFile            
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        resp = proc.communicate()[0]
        resp = str(resp)

        cmd = 'g++ -lsndfile '+outfileCpp+' -o '+self.binaryPath            
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        resp1 = proc.communicate()[0]
        print(type(resp))
        if 'ERROR' in resp:
            print (bcolors.FAIL+'>[ER]'+bcolors.ENDC+resp)
            return 2
        elif 'WARNING' in resp:
            print (bcolors.WARNING+'>[WA]'+bcolors.ENDC+resp)
            return 1

        else:
            print (bcolors.OKGREEN+'>[OK]'+bcolors.ENDC)
            return 0

    def openSVG(self):
        
        svgPath = os.path.join(self.dspDir,self.projectName+'-svg','process.svg')
        cmd = 'xdg-open '+svgPath
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # resp = proc.communicate()

    def getIR(self):
        lenSec = 0.5
        impOffsetSamps = 5000
        impLength = self.impLen
        imp = np.zeros(int(round(lenSec*self.sr)))
        imp[impOffsetSamps:impOffsetSamps+impLength] = 1
        self.processArray(imp)

        return

    def getLineResponse(self):
        line = np.linspace(-1,1,self.sr)
        self.processArray(line)
        return

    def processFile(self, tempPath):

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
        sr,y = wavfile.read(self.outputPath)
        n = range(len(y))
        x = self.inputSignal
        
        fig = plt.gcf()
        plt.clf()
        
        plt.subplot(3,1,1)
        plt.plot(n,x, color='black')
        plt.plot(n,y, color='red', alpha=0.7)
        plt.grid()
        plt.legend(['input', 'output'])

        plt.subplot(3,1,2)
        Pxx, freqs, bins, im = plt.specgram(y, NFFT=1024, Fs=self.sr,noverlap=100, cmap=plt.cm.gist_heat)

        plt.subplot(3,1,3)
        f, Pxx_den = sig.welch(y, self.sr, nperseg=1024)
        plt.semilogx(f,Pxx_den)



        plt.show()
        plt.pause(0.05)


    def getSpec(self):
        x = self.inputSignal
        f, Pxx_den = sig.welch(x, self.sr, nperseg=1024)

global MyDspHandler
MyDspHandler = DspFileHandler(dspFile,svg=svg, ir=ir, af=af, line=line, impLen=impLen)

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print ("Creating:", event.pathname)

    def process_IN_DELETE(self, event):
        print ("Removing:", event.pathname)

    def process_IN_CLOSE_WRITE(self,event):
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


