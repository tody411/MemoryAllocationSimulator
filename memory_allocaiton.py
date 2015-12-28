# -*- coding: utf-8 -*-
## @package memory_allocaiton
#
#  This package simulates common memory allocation strategies.
#  @author      tody
#  @date        2015/12/25

import numpy as np
import matplotlib.pyplot as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import sys
import random


## Memory Block Information.
class MemoryBlock:
    colors = [np.array([0.5, 0.9, 0.7]),
              np.array([1.0, 0.9, 0.5]),
              np.array([0.4, 0.4, 0.9])]

    def __init__(self, range, type="used"):
        self.range = range
        self.type = type

    ## Return the space of the memory block.
    def space(self):
        return self.range[1] - self.range[0]

    ## Return the type ID of the memory block.
    def typeID(self):
        if self.type == "used":
            return 0
        if self.type == "free":
            return 1
        if self.type == "fit":
            return 2
        return 0

    ## Paint override for the memory block.
    def paint(self, painter, x, y0, w, h_scale):
        y = y0 + h_scale * self.range[0]
        h = self.space() * h_scale

        gradient = QLinearGradient(x, y, x, y + h)

        color = self.colors[self.typeID()]
        dark_color = 0.85 * color

        gradient.setColorAt(0.0, QColor(255 * color[0], 255 * color[1], 255 * color[2]))
        gradient.setColorAt(0.7, QColor(255 * dark_color[0], 255 * dark_color[1], 255 * dark_color[2]))
        painter.setBrush(gradient)

        painter.drawRect(x, y, w, h)

        if self.typeID() == 2:
            painter.drawText(x + 0.5*w - 5, y + 0.5 * h + 5, "%s MB" % self.space())


## Memory information.
class Memory:
    def __init__(self, memory_size, used_blocks, free_blocks):
        self.memory_size = memory_size
        self.used_blocks = used_blocks
        self.free_blocks = free_blocks
        self.fit_blocks = []
        self.success = 0.0

    ## Copy the memory information.
    def copy(self):
        return Memory(self.memory_size, self.used_blocks, self.free_blocks)

    ## Return the free spaces of the memory.
    def freeSpaces(self):
        return [free_block.space() for free_block in self.free_blocks]

    ## Fit the requested memory blocks to the free spaces.
    def fit(self, memory_requests, fit_func):
        success, fit_blocks = fit_func(self.freeSpaces(), memory_requests)
        self.setFitBlocks(fit_blocks)
        self.success = success

    ## Set memory blocks to the free spaces.
    def setFitBlocks(self, fit_blocks):
        for i, fit_blocks_i in enumerate(fit_blocks):
            fit_address = self.free_blocks[i].range[0]
            for fit_block in fit_blocks_i:
                block = MemoryBlock((fit_address, fit_address + fit_block), "fit")
                self.fit_blocks.append(block)
                fit_address += fit_block

    ## Paint override for the memory.
    def paint(self, painter, x, y, w, h):
        h_scale = h / float (self.memory_size)

        for memory_space in self.used_blocks:
            memory_space.paint(painter, x, y, w, h_scale)

        for memory_space in self.free_blocks:
            memory_space.paint(painter, x, y, w, h_scale)

        for memory_space in self.fit_blocks:
            if memory_space is not None:
                memory_space.paint(painter, x, y, w, h_scale)


## Memory requests.
class MemoryRequests:
    def __init__(self, memory_size, memory_requests):
        self.memory_size = memory_size
        self.memory_requests = memory_requests

    ## Paint override for the requested memory blocks.
    def paint(self, painter, x, y, w, h):
        h_scale = h / float(self.memory_size)

        hi = 20
        for memory_request in self.memory_requests:
            memory_space = MemoryBlock((hi, hi + memory_request), "fit")
            memory_space.paint(painter, x, y, w, h_scale)
            hi += memory_request + 20


## Return memory status randomly assigned to 'use' or 'free'.
def randomAssignedMemory(memory_size=1000, fragment_min=10, fragment_max=100):
    memory_lists = []
    total = 0
    while total < memory_size:
        memory_lists.append(total)
        total += random.randint(fragment_min, fragment_max)

    memory_lists.append(memory_size)

    used_blocks = [MemoryBlock((memory_lists[i], memory_lists[i+1]), "used") for i in range(0, len(memory_lists) - 1, 2)]
    free_blocks = [MemoryBlock((memory_lists[i], memory_lists[i+1]), "free") for i in range(1, len(memory_lists)-1, 2)]

    return Memory(memory_size, used_blocks, free_blocks)


## Return requested memory blocks for the free available spaces.
def requestsMemories(free_spaces):
    memory_size  = 0.8 * np.sum(free_spaces)
    fragment_min = np.min(free_spaces) / 3
    fragment_max = np.max(free_spaces)

    memory_requests = []
    total = 0
    while total < memory_size:
        memory_request = random.randint(fragment_min, fragment_max)
        memory_requests.append(memory_request)
        total += memory_request
    return memory_requests


## Common part of fit functions.
def commonFit(free_spaces, memory_requests, fit_func):
    fit_spaces = np.zeros(len(free_spaces))
    fit_blocks = [[] for i in range(len(free_spaces))]
    num_fitted = 0

    for memory_request in memory_requests:
        fitted = fit_func(free_spaces, memory_request, fit_spaces, fit_blocks)
        num_fitted += fitted

    success = num_fitted / float(len(memory_requests))
    return success, fit_blocks


## First-Fit implementation.
def firstFit(free_spaces, memory_requests):
    def fit_func(free_spaces, memory_request, fit_spaces, fit_blocks):
        for i in range(len(free_spaces)):
            if fit_spaces[i] + memory_request < free_spaces[i]:
                fit_blocks[i].append(memory_request)
                fit_spaces[i] += memory_request
                return 1
        return 0

    return commonFit(free_spaces, memory_requests, fit_func)


## Best-Fit implementation.
def bestFit(free_spaces, memory_requests):
    def fit_func(free_spaces, memory_request, fit_spaces, fit_blocks):
        free_min = 1000
        fit_id = -1
        for i in range(len(free_spaces)):
            if fit_spaces[i] + memory_request < free_spaces[i]:
                free_space = free_spaces[i] - (fit_spaces[i] + memory_request)
                if free_space < free_min:
                    free_min = free_space
                    fit_id = i
        if fit_id > -1:
            fit_blocks[fit_id].append(memory_request)
            fit_spaces[fit_id] += memory_request
            return 1
        return 0

    return commonFit(free_spaces, memory_requests, fit_func)


## Worst-Fit implementation.
def worstFit(free_spaces, memory_requests):
    def fit_func(free_spaces, memory_request, fit_spaces, fit_blocks):
        free_max = 0
        fit_id = -1
        for i in range(len(free_spaces)):
            if fit_spaces[i] + memory_request < free_spaces[i]:
                free_space = free_spaces[i] - (fit_spaces[i] + memory_request)
                if free_space > free_max:
                    free_max = free_space
                    fit_id = i

        if fit_id > -1:
            fit_blocks[fit_id].append(memory_request)
            fit_spaces[fit_id] += memory_request
            return 1
        return 0

    return commonFit(free_spaces, memory_requests, fit_func)


## Generate a matplot figure to plot the comparison data of: First-Fit, Best-Fit, and Worst-Fit.
def memoryAllocationComparison(num_comparison=50):
    data={}
    data["best_fit"] = []
    data["first_fit"] = []
    data["worst_fit"] = []
    for i in xrange(num_comparison):
        memory = randomAssignedMemory()
        free_spaces = memory.freeSpaces()
        memory_requests = requestsMemories(free_spaces)

        data["best_fit"].append(bestFit(free_spaces, memory_requests)[0])
        data["first_fit"].append(firstFit(free_spaces, memory_requests)[0])
        data["worst_fit"].append(worstFit(free_spaces, memory_requests)[0])

    xs = np.arange(num_comparison)
    plt.plot(xs, data["best_fit"], label='Best-Fit: %s' % np.average(data["best_fit"]))
    plt.plot(xs, data["first_fit"], label='First-Fit: %s' % np.average(data["first_fit"]))
    plt.plot(xs, data["worst_fit"], label='Worst-Fit: %s' % np.average(data["worst_fit"]))

    plt.legend()
    plt.show()


## GUI of memory allocation simulator.
#  * mouse click: simulate a memory allocation process with a new memory status.
class MemoryAllocationSimulator(QWidget):

    def __init__(self, master=None):
        super(MemoryAllocationSimulator, self).__init__(master)
        self.setWindowTitle("Memory Allocation Simulator")
        self._simulate()

    ## Paint override: MemoryRequests, 3 Memory objects (First-Fit, Best-Fit, Worst-Fit).
    def paintEvent(self, ev):
        painter = QPainter(self)
        painter.begin(self)

        h = self.height() - 40
        w = self.width() / 5
        painter.drawText(20, 20, "Memory Requests")
        self._requests.paint(painter, 20, 30, w, h)

        x = 40 + w

        labels = ["First-Fit", "Best-Fit", "Worst-Fit"]

        for label, memory in zip(labels, self._memories):
            painter.drawText(x, 20, label + ": %s" % memory.success)
            memory.paint(painter, x, 30, w, h)
            x += w + 20

        painter.end()

    ## Next simulation by mouse clicking.
    def mousePressEvent(self, e):
        self._simulate()
        self.update()

    ## Simulate with a new memory status.
    def _simulate(self):
        memory_size = 1000
        memory = randomAssignedMemory(memory_size, 20, 200)
        self._memories = [memory, memory.copy(), memory.copy()]

        free_spaces = memory.freeSpaces()
        memory_requests = requestsMemories(free_spaces)
        self._requests = MemoryRequests(memory_size, memory_requests)

        fits = [firstFit, bestFit, worstFit]
        for memory, fit_func in zip(self._memories, fits):
            memory.fit(memory_requests, fit_func)


## Main function to run GUI.
def main():
    app = QApplication(sys.argv)
    widget = MemoryAllocationSimulator()
    widget.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    memoryAllocationComparison()
