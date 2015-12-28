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


## Int attribute.
class IntAttribute:
    def __init__(self, name="", val=0, val_min=0, val_max=100):
        self._name = name
        self._val = val
        self._val_min = val_min
        self._val_max = val_max

    def name(self):
        return self._name

    def setValue(self, val):
        self._val = val

    def value(self):
        return self._val

    def validator(self, parent=None):
        return QIntValidator(self._val_min, self._val_max, parent)


## Simulation setting.
class SimulationSetting:
    def __init__(self):
        self.memory_size = IntAttribute("Memory Size", 1000, 500, 2000)
        self.block_min = IntAttribute("Memory Block Min", 50, 10, 100)
        self.block_max = IntAttribute("Memory Block Max", 200, 100, 500)
        self.num_trials = IntAttribute("Num Trials", 50, 5, 10000)


## Return random memory status with several 'use' or 'free' blocks.
#
#  @param memory_size     total memory size.
#  @param block_min    minimum size of each memory block.
#  @param block_max    maximum size of each memory block.
#  @retval Memory instance.
def randomMemoryStatus(memory_size=1000, block_min=10, block_max=100):
    memory_lists = []
    total = 0
    while total < memory_size:
        memory_lists.append(total)
        total += random.randint(block_min, block_max)

    memory_lists.append(memory_size)

    used_blocks = [MemoryBlock((memory_lists[i], memory_lists[i+1]), "used") for i in range(0, len(memory_lists) - 1, 2)]
    free_blocks = [MemoryBlock((memory_lists[i], memory_lists[i+1]), "free") for i in range(1, len(memory_lists)-1, 2)]

    return Memory(memory_size, used_blocks, free_blocks)


## Return requested memory blocks for the free available spaces.
#
#  @param free_spaces list of free available spaces.
#  @retval    list of requested memory sizes.
def requestsMemories(free_spaces):
    memory_size  = 0.8 * np.sum(free_spaces)
    block_min = np.min(free_spaces) / 3
    block_max = np.max(free_spaces)

    memory_requests = []
    total = 0
    while total < memory_size:
        memory_request = random.randint(block_min, block_max)
        memory_requests.append(memory_request)
        total += memory_request
    return memory_requests


## Common part of fit functions.
#  @param free_spaces list of free available spaces.
#  @param memory_requests   list of requested memory sizes.
#  @param fit_func          memory allocation function to implement.
#  @retval success success rate.
#  @retval fit_blocks list of fitted memory block sizes.
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
def runSimulationTrials(num_trials=50, memory_size=1000, block_min=10, block_max=100):
    plt.title("Memory Allocation Simulation: %s Trials" %num_trials)

    fit_strategies = [("first_fit", "First-Fit", firstFit),
                      ("best_fit", "Best-Fit", bestFit),
                      ("worst_fit", "Worst-Fit", worstFit)]

    data={}

    for fit_strategy in fit_strategies:
        data[fit_strategy[0]] = []

    for i in xrange(num_trials):
        memory = randomMemoryStatus(memory_size, block_min, block_max)
        free_spaces = memory.freeSpaces()
        memory_requests = requestsMemories(free_spaces)

        for fit_strategy in fit_strategies:
            data[fit_strategy[0]].append(fit_strategy[2](free_spaces, memory_requests)[0])

    xs = np.arange(num_trials)

    for fit_strategy in fit_strategies:
        success_rates = data[fit_strategy[0]]
        success_rates_avg = np.average(success_rates)
        label = '%s: %s%%' %(fit_strategy[1], round(100*success_rates_avg, 2))
        plt.plot(xs, success_rates, label=label)

    plt.ylabel("Success Rates")
    plt.xlabel("Trials")

    plt.legend()
    plt.show()


## GUI for simulation setting.
class SimulationSettingUI(QWidget):

    def __init__(self, setting):
        super(SimulationSettingUI, self).__init__()
        self._setting = setting
        self.createUI()
        self.setWindowTitle("Simulation Setting")

    ## Create input GUI for simulation setting.
    def createUI(self):
        attributes = [self._setting.memory_size,
                      self._setting.block_min,
                      self._setting.block_max,
                      self._setting.num_trials]

        layout = QGridLayout()
        for i, attribute in enumerate(attributes):
            label = QLabel(attribute.name())
            value_edit = QLineEdit()
            value_edit.setText("%s" % attribute.value())
            value_edit.editingFinished.connect(self.valueEditChanged(value_edit, attribute.setValue))
            value_edit.setValidator(attribute.validator())
            label.setBuddy(value_edit)

            layout.addWidget(label, i, 0)
            layout.addWidget(value_edit, i, 1)

        self.setLayout(layout)

    ## Callback for the value_edit and setter.
    def valueEditChanged(self, value_edit, setter):
        def func():
            val = int(value_edit.text())
            setter(val)
        return func


## GUI of memory allocation simulator.
#  * mouse click: simulate a memory allocation process with a new memory status.
class SimulatorView(QWidget):

    def __init__(self, setting, parent=None):
        super(SimulatorView, self).__init__(parent)
        self._setting = setting
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
            painter.drawText(x, 20, label + ": %s%%" % round(100 * memory.success, 1))
            memory.paint(painter, x, 30, w, h)
            x += w + 20

        painter.end()

    ## Next simulation will be driven by mouse clicking.
    def mousePressEvent(self, e):
        self._simulate()
        self.update()

    ## Simulate with a new memory status.
    def _simulate(self):
        memory_size = self._setting.memory_size.value()
        memory = randomMemoryStatus(memory_size,
                                      self._setting.block_min.value(),
                                      self._setting.block_max.value())
        self._memories = [memory, memory.copy(), memory.copy()]

        free_spaces = memory.freeSpaces()
        memory_requests = requestsMemories(free_spaces)
        self._requests = MemoryRequests(memory_size, memory_requests)

        fits = [firstFit, bestFit, worstFit]
        for memory, fit_func in zip(self._memories, fits):
            memory.fit(memory_requests, fit_func)


## Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Memory Allocation Simulator")
        self._setting = SimulationSetting()

        view = SimulatorView(self._setting)

        self._setting_ui = SimulationSettingUI(self._setting)
        self.setCentralWidget(view)
        self.createMenu()

    def createMenu(self):
        menu_bar = self.menuBar()
        simulation_menu = QMenu("Simulation", self)
        simulation_menu.addAction("Setting GUI", self._showSettingUI)
        simulation_menu.addAction("Run Simulation Trials", self._runSimulationTrials)
        menu_bar.addMenu(simulation_menu)

    def closeEvent(self, event):
        QApplication.closeAllWindows()
        return QMainWindow.closeEvent(self, event)

    def _runSimulationTrials(self):
        num_trials = self._setting.num_trials.value()
        memory_size = self._setting.memory_size.value()
        block_min = self._setting.block_min.value()
        block_max = self._setting.block_max.value()
        runSimulationTrials(num_trials, memory_size, block_min, block_max)

    def _showSettingUI(self):
        self._setting_ui.show()


## Main function to show main window.
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
