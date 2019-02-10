#!/usr/bin/env python

#title           : faustwatch.py
#description     : utilities for FAUST development
#author          : Patrik Lechner <ptrk.lechner@gmail.com>
#date            : Jan 2018
#version         : 1.2.0
#usage           :
#notes           :
#python_version  : 3.6.3
#=======================================================================
from __future__ import print_function
__author__ = "Patrik Lechner <ptrk.lechner@gmail.com>"

import pyinotify
import subprocess,shlex
import os
import numpy as np
from scipy.io import wavfile
import matplotlib
import argparse

from pyo import Server,SfPlayer

import config
import plotlib as pl
import logging

logging.captureWarnings(True)
logging.basicConfig(level=logging.CRITICAL)

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

parser.add_argument('--impLen', type=int, default = 1, help='Length of impulse in samples. Default is unit impulse, so 1.')

parser.add_argument('--length', type=float, default=1,
                    help='File Length in seconds. Default 0.5')

# Hotfix: disableBroken: line feature
# parser.add_argument('--line', dest='line', action='store_const',
#                     const=True, default=False,
#                     help='Get response to line from -1 to 1. So input-output amplitude relationship. Useful for plotting transfer functions of non-linearities')


args = parser.parse_args()
dspFile = args.dspFile
svg = args.svg
ir = args.ir
impLen = args.impLen
lenSec = float(args.length)

logging.debug(lenSec)

# Hotfix: disableBroken: line feature
# line = args.line
line = False

try:
    af = args.af[0]
except:
    af = ''

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
    def __init__(self, dspFile, svg=False, ir=False, af='', line=False, impLen=1, lenSec = 0.5, plotter=None):
        self.svg = svg
        self.dspFile = dspFile
        self.ir = ir
        self.af =af
        self.line=line
        self.lenSec = lenSec
        self.impLen = impLen
        self.sr = 44100.
        self.lenSamps = int(round(self.lenSec*self.sr))
        self.audioInitialized = False
        self.irAvailable = False

        logging.debug(self.lenSamps)

        self.lastIR = np.zeros(self.lenSamps)
        self.lastSpec = None
        self.lastLine = None

        self.dspDir = os.path.dirname(os.path.abspath(dspFile))
        self.baseName = os.path.basename(dspFile)
        self.projectName = self.baseName[:-4]
        self.outputPath= config.audioOutPath 
        self.inputPath= config.audioInPath
        self.plotter = plotter

        logging.info('watching file: '+os.path.abspath(dspFile))

    def initializeAudio(self):
        self.audioServer = Server(audio='jack')
        self.audioServer.boot()
        self.audioServer.start()
        self.reloadAudioFile()
        self.audioInitialized = True

    def dummy(self):
        return
    
    def reloadAudioFile(self):
        self.sfplayer = SfPlayer(self.outputPath, loop=False, mul=1).out()        

    def checkCompileResponseAndTakeAction(self,response,successAction):
        resp = response.decode("utf-8")
        if 'error' in resp.lower():
            print(bcolors.FAIL+'>[ER]'+bcolors.ENDC+resp)
            return 2
        elif 'warning' in resp.lower():
            print(bcolors.WARNING+'>[WA]'+bcolors.ENDC+resp)
            successAction()
            return 1
        else:
            print(resp)
            print(bcolors.OKGREEN+'>[OK]'+bcolors.ENDC)
            successAction()
            return 0

    def compute(self):
        if not self.svg and not self.ir and not self.af and not self.line:
            logging.info('only compiling, no other action.')

            cmd = 'faust '+self.dspFile
            cmd = shlex.split(cmd)
            proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            resp = proc.communicate()[0]
            self.checkCompileResponseAndTakeAction(resp,self.dummy)

        if self.svg:
            cmd = 'faust --svg '+self.dspFile
            cmd = shlex.split(cmd)
            proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            resp = proc.communicate()[0]
            self.checkCompileResponseAndTakeAction(resp, self.openSVG)

        if self.ir:
            returnCode = self.compile()
            if returnCode <2:
                self.getIR()
                self.plotSignalQt()
          
        if self.line:
            returnCode = self.compile()
            if returnCode <2:
                self.getLineResponse()
                self.plotSignalQt()

        if len(self.af)>0:
            returnCode = self.compile()
            if returnCode<2:
                self.inputPath = self.af
                self.sr, self.inputSignal = wavfile.read(self.af)
                self.processFile(self.af)
                self.plotSignalQt()

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
        resp = proc.communicate()[0]
        returnCode = self.checkCompileResponseAndTakeAction(resp,self.dummy)
        return returnCode

    def openSVG(self):
        
        svgPath = os.path.join(self.dspDir,self.projectName+'-svg','process.svg')
        cmd = 'xdg-open '+svgPath
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def getIR(self):
        impOffsetSamps = int(round(self.lenSamps*0.25))
        impLength = self.impLen
        imp = np.zeros(self.lenSamps)
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
        self.irAvailable = True
        if not self.audioInitialized:
            self.initializeAudio()
        self.play()
        return
    
    def processArray(self,anArray, sr=44100,inputPath='/tmp/offlineInput.wav'):
        assert type(anArray) ==np.ndarray
        self.inputSignal = anArray.astype(np.float32)
        wavfile.write(inputPath, sr, anArray)
        self.inputPath = inputPath
        
        cmd = os.path.join(self.dspDir,self.binaryPath)+' '+inputPath+' '+self.outputPath            
        cmd = shlex.split(cmd)
        proc = subprocess.Popen(cmd,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        resp = proc.communicate()[0]

        if not self.audioInitialized:
            self.initializeAudio()
        self.play()

        return

    def play(self):
        logging.debug('play function called')
        self.reloadAudioFile()
        
    def plotSignalQt(self):
        _, y = wavfile.read(self.outputPath)
        if y.dtype != np.float64:
            if y.dtype==np.int16:
                y = y.astype(np.float64)/(2**15)
            else:
                y = y.astype(np.float64)
        if not len(self.lastIR)==len(y):
            self.lastIR = np.zeros_like(y)
        
        currentAndLast = np.array([self.lastIR,y]).T

        self.plotter.plot(currentAndLast)
        self.lastIR = y
        return

global MyDspHandler

if ir or len(af)>1:
    plotter = pl.Plotter()
    MyDspHandler = DspFileHandler(
        dspFile, svg=svg, ir=ir, af=af, line=line, impLen=impLen, plotter=plotter, lenSec=lenSec)
else:
    MyDspHandler = DspFileHandler(
        dspFile, svg=svg, ir=ir, af=af, line=line, impLen=impLen, plotter=None, lenSec=lenSec)

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


