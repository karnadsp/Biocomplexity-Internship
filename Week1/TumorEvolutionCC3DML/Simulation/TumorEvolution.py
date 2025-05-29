import sys
from os import environ
from os import getcwd
import math
from math import *
import string

#parameter scan variables
PROBMUT = 0.1
CADHSTDEV = 2.0
RANDOMSEED = 2284322


sys.path.append(environ["PYTHON_MODULE_PATH"])

pi=math.pi

    
class Parameters:
    def __init__(self):


        # modified to match original ugly code
        self.V0 = 16. # tumor cell target volume
        self.S0 = 16. # tumor cell target surface
        self.LBD_V0 = 15.# tumor cell volume constraint lambda
        self.LBD_S0 = 5. # tumor cell surface constraint lambda
        self.incvol = 0.2 # growth rate of tumor cells in pixels/MCS
        self.decvol = 0.01 # decreasing rate of tumor cells in pixels/MCS
        self.deadvol = 0.5 # final dead cell volume fraction
        self.volmaxmit = 2.0*self.V0 # tumor cell mitosis volume
        self.Svolmaxmit = 2.0*self.V0 # stem cell mitosis volume 
        self.ktgs = 4. # factor multiplying: surface = ktgs*sqrt(volume)
        self.maxdiv = 8 # =8 maximum number of cell divisions
        self.probstem = 0.2 # =0.20 probability of new stem cell after division  
        global PROBMUT,CADHSTDEV
        self.probmut = PROBMUT # J-CADH probability of mutation
        self.cadhstdev = CADHSTDEV # J-CADH gaussian distribution standard deviation
        
#         self.probmut = 0.1 # J-CADH probability of mutation
#         self.cadhstdev = 0.5 # J-CADH gaussian distribution standard deviation
        

        # # THRESHOLDS
        self.MCSThr = 50   # initial relaxation # of MCS
        self.PGrThr0 = 0.032  # concetration above which proliferating cell grows
        self.PNeThr0 = 102.0 #.total damage at which:proliferating -> necrotic
        self.QPThr0 = 15.9*5  # total happiness at which: quiescent -> proliferating
        self.QNeThr0 = 2.0*102.0  # total damage at which: quiescent -> necrotic
        self.SGrThr0 = 0.032  # stem growth threshold
        self.SNeThr0 = 2.0*204.0 # total damage at which: stem -> necrotic  
        self.QSSThr0 = 15.9*5  # total happiness at which: QS -> S
        self.QSNeThr0 = 2.0*self.SNeThr0 # total damage at which: quiescent -> necrotic

        self.GluD = 0.032  # Glucose concentration below which damage accumulates --- 0.5mM --> 0.032 fmol/vox
        self.GluK = 0.00256 # Michaelis-Menten constant for glucose concentration = 0.04 mM --> 2.56e-18 mol/vox --> 0.00256 fmol/vox
        self.PUgMax = 2.25 # Proliferating cell - Glucose maximum uptaken rate = 10e-17 mol/cell/sec --> 2.25e-15 fmol/vox/MCS
        self.QUgMax = 1.69 # Quiescent cell - Glucose maximum uptaken rate = 0.75*2.25e-15 fmol/vox/MCS = 1.69 fmol/vox/MCS
        self.SUgMax = 2.25 # Stem cell - Glucose maximum uptaken rate
        self.QSUgMax = 1.69 # QStem cell - Glucose maximum uptaken rate = 0.75*2.25e-15 fmol/vox/MCS = 1.69 fmol/vox/MCS


parameters=Parameters()
        
import CompuCellSetup

sim,simthread = CompuCellSetup.getCoreSimulationObjects()

# configureSimulation(sim)

pyAttributeAdder,dictionaryAdder=CompuCellSetup.attachDictionaryToCells(sim)
CompuCellSetup.initializeSimulationObjects(sim,simthread)

#
#Add Python steppables here
#
from PySteppables import SteppableRegistry
steppableRegistry=SteppableRegistry()
#
# GROWTH, SHRINKAGE, DEATH
#
from TumorEvolution_steppable import GrowthSteppable
growthSteppable=GrowthSteppable(sim,1)
growthSteppable.initParameters(parameters)
#    
steppableRegistry.registerSteppable(growthSteppable)
#
# MITOSIS, MUTATION
#
from TumorEvolution_steppable import MitosisSteppable
mitosisSteppable=MitosisSteppable(sim,1)
mitosisSteppable.initParameters(parameters)
steppableRegistry.registerSteppable(mitosisSteppable)
#
# DAMAGE/HEALTH ACCUMULATOR
#
from TumorEvolution_steppable import StarvationDamageAcumulator
starvationDamageAcumulator=StarvationDamageAcumulator(sim,1)
starvationDamageAcumulator.initParameters(parameters)
steppableRegistry.registerSteppable(starvationDamageAcumulator)
#
# CELL TYPE TRANSITION
#
from TumorEvolution_steppable import TypeTransitionSteppable
typeTransitionSteppable=TypeTransitionSteppable(sim,1)
typeTransitionSteppable.initParameters(parameters)
steppableRegistry.registerSteppable(typeTransitionSteppable)


from TumorEvolution_steppable import DataOutput
instanceOfDataOutput=DataOutput(_simulator=sim,_frequency=1000)
instanceOfDataOutput.initParameters(parameters)
steppableRegistry.registerSteppable(instanceOfDataOutput)

CompuCellSetup.mainLoop(sim,simthread,steppableRegistry)
