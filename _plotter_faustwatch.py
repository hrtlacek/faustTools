# -*- coding: utf-8 -*-

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
import zmq
import time
import pickle
import codecs
import sys

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


plt = pg.plot()
plt.setWindowTitle('pyqtgraph example: Legend')
plt.addLegend()

# c1 = plt.plot([1, 3, 2, 4], pen='r', symbol='o',
#   symbolPen='r', symbolBrush=0.5, name='red plot')

c1 = plt.plot([1, 2, 3, 4],  pen='w')
plt.showGrid(x=True, y=True)

plots.append(c1)
# c2 = plt.plot([2, 1, 4, 3], pen='g', fillLevel=0,
#   fillBrush=(255, 255, 255, 30), name='green plot')

colors = ['r', 'g', 'b', 'y', 'w']


def update():

    try:
        js = socket.recv_json(flags=1)
        # print(js)
        socket.send(b"World")

        if js['type'] == 'data':
            arr = pickle.loads(js['data'].encode('latin-1'))
            nPlots = getNPlots(arr)
            currNPlots = len(plots)
            diff = nPlots-currNPlots

            for i in range(diff):
                plots.append(plt.plot([0, 1, 2], pen=colors[i % len(colors)]))
            if nPlots > 1:
                for i in range(nPlots):
                    thisPlot = plots[i]
                    thisPlot.setData(arr[:, i])
            else:
                c1.setData(arr)
                try:
                    name = js['labels'][0]
                    c1.name = name
                    # plt.addLegend()
                except:
                    pass
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


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)

QtGui.QApplication.instance().exec_()
