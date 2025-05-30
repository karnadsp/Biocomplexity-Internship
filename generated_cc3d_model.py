from cc3d import CompuCellSetup
from cc3d.core.PySteppables import *


class SimulationSteppable(SteppableBasePy):

    def __init__(self, frequency=1):
        SteppableBasePy.__init__(self, frequency)

    def start(self):
        pass

    def step(self, mcs):
        pass

CompuCellSetup.register_steppable(steppable=SimulationSteppable(frequency=1))