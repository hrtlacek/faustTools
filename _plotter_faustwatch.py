# -*- coding: utf-8 -*-

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import zmq
import time
import pickle
import codecs
import sys
import scipy.signal as sig

import logging
logging.basicConfig(level=logging.DEBUG)
logging.debug('Logger process started.')

global plots
plots = []

# print (sys.argv)

try:
    port = sys.argv[1]
except IndexError:
    port = 5555

app = QtGui.QApplication([])

# =======NETWORK-INIT===============
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:"+str(port))

# ==========Graphics-INIT===========

# pg.setConfigOptions(antialias=True) #anti aliasing seems to slow down a lot
win = pg.GraphicsWindow(title="FAUSTwatch")
irPlot = win.addPlot()
irPlot.addLegend()
irPlot.setWindowTitle('pyqtgraph example: Legend')

c1 = irPlot.plot([1, 2, 3, 4],  pen='r', name='last IR', alpha=0.1)

plots.append(c1)
c2 = irPlot.plot([2, 1, 4, 3], pen='w', fillLevel=0,
  fillBrush=(255, 255, 255, 30), name='current IR', alpha = 0.5)
plots.append(c2)
irPlot.showGrid(x=True, y=True)

win.nextRow()
specPlot = win.addPlot()
specPlot.addLegend()

specPlot.setLogMode(True, False)

sp1 = specPlot.plot([0, 1, 2, 3], pen='r', name='last')
sp2 = specPlot.plot([0, 1, 2, 3], pen='w', name='current', fillLevel=-180,
                    fillBrush=(255, 255, 255, 30))
specPlots = [sp1,sp2]
irPlot.showGrid(x=True, y=True)



colors = ['r', 'g', 'b', 'y', 'w']


def update():

    try:
        js = socket.recv_json(flags=1)
        # print(js)
        socket.send(b"ok")

        if js['type'] == 'data':
            arr = pickle.loads(js['data'].encode('latin-1'))
            nPlots = getNPlots(arr)
            currNPlots = len(plots)
            diff = nPlots-currNPlots

            for i in range(diff):
                plots.append(irPlot.plot(
                    [0, 1, 2], pen=colors[i % len(colors)]))
            if nPlots > 1:
                for i in range(nPlots):
                    thisPlot = plots[i]
                    thisPlot.setData(arr[:, i])

                    thisSpec = specPlots[i]
                    spec,f = getSpec(arr[:,i])
                    thisSpec.setData(f,spec)
            else:
                c1.setData(arr)
                # try:
                #     name = js['labels'][0]
                #     c1.name = name
                #     # plt.addLegend()
                # except:
                #     pass
            # for i in range(nPlots)
            # print(arr)

        elif js['type'] == 'cmd':
            print('received command:', js['data'])

    except zmq.error.Again:
        pass

    return


def getNPlots(arr):
    try:
        nPlots = arr.shape[1]
    except:
        nPlots = 1
    return nPlots

def getSpec(arr):
    f, Pxx_den = sig.welch(arr, 44100, nperseg=1024)
    dbspec = aToDb(Pxx_den)
    return dbspec,f


def aToDb(a):
    db = np.clip(20*np.log10(a), -180, 99)
    return db

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)

QtGui.QApplication.instance().exec_()
