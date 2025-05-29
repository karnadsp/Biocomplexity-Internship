from math import sqrt
import sys
import os
#epithelial cell parameters
pL=0.60
pB=0.20
pA=1-pL-pB
leng_dm1=20#height of the cell
bre_dm1 =10#width of the cell
#ecm parameters
ecto_wd=10
ecto_ht=7
#number of cells along the rostral-caudal axis
global Nx,Ny,g,Lx,Ly,m
Nset=115
Necto=Nset
Nx=Nset
wall_w=3
Ny=1
Lx=Nx*bre_dm1+2*wall_w#lattice dimensions along the rostral-caudal axis 
Ly=ecto_ht+(Ny+2)*15-5#lattice dimensions along dorsal-ventral axis, enough to fit the layer
####################
lambda_v=10#volume constraint (lambda_v) as in Eq.2 
LamFP_c=50#strength of internal (lambda_i) focal links as in Eq.3
LamFP_j=20#strength of apical external (lambda_a) focal links as in Eq.5
#basal external links (lambda_b) set to fixed 100 in steppables
max_lambda=600#maximum value of lambda_a 
cutoff=7500#breaking tension
rate=0.05#rate of apical contractility
wave_speed=300#wave speed (W)
end_time=500000#total time for the simulation, set to be large
##exit condition in the steppables simulation
relax_time=50#relaxation time for the simulation
global end_time
####################
def configureSimulation(sim):
	import CompuCellSetup
	from XMLUtils import ElementCC3D
	CompuCell3DElmnt=ElementCC3D("CompuCell3D",{"Revision":"20160527","Version":"3.7.5"})
	PottsElmnt=CompuCell3DElmnt.ElementCC3D("Potts")
	# Basic CPM properties
	PottsElmnt.ElementCC3D("Dimensions",{"x":Lx,"y":Ly,"z":"1"})
	PottsElmnt.ElementCC3D("Steps",{},end_time)
	PottsElmnt.ElementCC3D("Temperature",{},"60.0")
	PottsElmnt.ElementCC3D("NeighborOrder",{},"2")
	PluginElmnt=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"CellType"})
	# Listing all cell types in the simulation
	PluginElmnt.ElementCC3D("CellType",{"TypeId":"0","TypeName":"Medium"})
	PluginElmnt.ElementCC3D("CellType",{"TypeId":"1","TypeName":"lateral_a"})
	PluginElmnt.ElementCC3D("CellType", {"TypeId": "2", "TypeName": "basal_a"})
	PluginElmnt.ElementCC3D("CellType", {"TypeId": "3", "TypeName": "apical_a"})
	PluginElmnt.ElementCC3D("CellType",{"TypeId":"4","TypeName":"ecm"})
	PluginElmnt.ElementCC3D("CellType", {"TypeId": "5", "TypeName": "wall"})
	CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"Volume"})
	# Calling Plugin related to finding Center of Masses for the cells
	PluginElmnt_1=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"CenterOfMass"})
	# Specifying contact energies as in Table 4
	contact = CompuCell3DElmnt.ElementCC3D("Plugin", {"Name": "Contact"})
	contact.ElementCC3D("Energy", {"Type1": "Medium", "Type2": "Medium"}, 100.9)
	contact.ElementCC3D("Energy", {"Type1": "Medium", "Type2": "lateral_a"}, 100.9)
	contact.ElementCC3D("Energy", {"Type1": "Medium", "Type2": "basal_a"}, 100.9)
	contact.ElementCC3D("Energy", {"Type1": "Medium", "Type2": "apical_a"}, 80.6)
	contact.ElementCC3D("Energy", {"Type1": "Medium", "Type2": "ecm"}, 100.9)
	contact.ElementCC3D("Energy", {"Type1": "Medium", "Type2": "wall"}, 69.4)
	##
	contact.ElementCC3D("Energy", {"Type1": "lateral_a", "Type2": "lateral_a"}, 83.4)
	contact.ElementCC3D("Energy", {"Type1": "lateral_a", "Type2": "basal_a"}, 100.9)
	contact.ElementCC3D("Energy", {"Type1": "lateral_a", "Type2": "apical_a"}, 100.9)
	contact.ElementCC3D("Energy", {"Type1": "lateral_a", "Type2": "ecm"}, 100.9)
	contact.ElementCC3D("Energy", {"Type1": "lateral_a", "Type2": "wall"}, 100.9)
	##
	contact.ElementCC3D("Energy", {"Type1": "basal_a", "Type2": "basal_a"}, 83.4)
	contact.ElementCC3D("Energy", {"Type1": "basal_a", "Type2": "apical_a"}, 100.9)
	contact.ElementCC3D("Energy", {"Type1": "basal_a", "Type2": "ecm"}, 80.6)
	contact.ElementCC3D("Energy", {"Type1": "basal_a", "Type2": "wall"}, 100.9)
	##
	contact.ElementCC3D("Energy", {"Type1": "apical_a", "Type2": "apical_a"}, 100.9)
	contact.ElementCC3D("Energy", {"Type1": "apical_a", "Type2": "ecm"}, 100.9)
	contact.ElementCC3D("Energy", {"Type1": "apical_a", "Type2": "wall"}, 100.9)
	##
	contact.ElementCC3D("Energy", {"Type1": "ecm", "Type2": "ecm"}, 83.4)
	contact.ElementCC3D("Energy", {"Type1": "ecm", "Type2": "wall"}, 100.9)
	##
	contact.ElementCC3D("Energy", {"Type1": "wall", "Type2": "wall"}, 0)
	contact.ElementCC3D("NeighborOrder", {}, 4)

	#focal Point PLasticity
	#Specifying focal point plasticity parameters
	fpp=CompuCell3DElmnt.ElementCC3D("Plugin",{"Name":"FocalPointPlasticity"})
	fpp.ElementCC3D("Local")
	#Links between internal compartments
	InternalParametersElmnt_7 = fpp.ElementCC3D("InternalParameters", {"Type1": "basal_a", "Type2": "apical_a"})
	InternalParametersElmnt_7.ElementCC3D("Lambda", {}, "0")
	InternalParametersElmnt_7.ElementCC3D("ActivationEnergy", {}, "-50")
	InternalParametersElmnt_7.ElementCC3D("TargetDistance", {}, "0")
	InternalParametersElmnt_7.ElementCC3D("MaxDistance", {}, "200")
	InternalParametersElmnt_7.ElementCC3D("MaxNumberOfJunctions", {"NeighborOrder": "6"}, "0")

	InternalParametersElmnt_7 = fpp.ElementCC3D("InternalParameters", {"Type1": "basal_a", "Type2": "lateral_a"})
	InternalParametersElmnt_7.ElementCC3D("Lambda", {}, "0")
	InternalParametersElmnt_7.ElementCC3D("ActivationEnergy", {}, "-50")
	InternalParametersElmnt_7.ElementCC3D("TargetDistance", {}, "0")
	InternalParametersElmnt_7.ElementCC3D("MaxDistance", {}, "200")
	InternalParametersElmnt_7.ElementCC3D("MaxNumberOfJunctions", {"NeighborOrder": "6"}, "0")

	InternalParametersElmnt_7 = fpp.ElementCC3D("InternalParameters", {"Type1": "lateral_a", "Type2": "apical_a"})
	InternalParametersElmnt_7.ElementCC3D("Lambda", {}, "0")
	InternalParametersElmnt_7.ElementCC3D("ActivationEnergy", {}, "-50")
	InternalParametersElmnt_7.ElementCC3D("TargetDistance", {}, "0")
	InternalParametersElmnt_7.ElementCC3D("MaxDistance", {}, "200")
	InternalParametersElmnt_7.ElementCC3D("MaxNumberOfJunctions", {"NeighborOrder": "6"}, "0")

	#Parameters between external compartments
	ParametersElmnt = fpp.ElementCC3D("Parameters", {"Type1": "basal_a", "Type2": "basal_a"})
	ParametersElmnt.ElementCC3D("Lambda", {}, "0")
	ParametersElmnt.ElementCC3D("ActivationEnergy", {}, "-50")
	ParametersElmnt.ElementCC3D("TargetDistance", {}, "0")
	ParametersElmnt.ElementCC3D("MaxDistance", {}, "0")
	ParametersElmnt.ElementCC3D("MaxNumberOfJunctions", {"NeighborOrder": "6"}, "0")

	ParametersElmnt = fpp.ElementCC3D("Parameters", {"Type1": "apical_a", "Type2": "apical_a"})
	ParametersElmnt.ElementCC3D("Lambda", {}, "0")
	ParametersElmnt.ElementCC3D("ActivationEnergy", {}, "-50")
	ParametersElmnt.ElementCC3D("TargetDistance", {}, "0")
	ParametersElmnt.ElementCC3D("MaxDistance", {}, "0")
	ParametersElmnt.ElementCC3D("MaxNumberOfJunctions", {"NeighborOrder": "6"}, "0")
	
	#Plugin to find nearest neighbors
	ntp =CompuCell3DElmnt.ElementCC3D("Plugin", {"Name": "NeighborTracker"})
	CompuCellSetup.setSimulationXMLDescription(CompuCell3DElmnt)
	CompuCellSetup.setSimulationXMLDescription(CompuCell3DElmnt)

import sys
from os import environ
from os import getcwd
import string
sys.path.append(environ["PYTHON_MODULE_PATH"])

import CompuCellSetup

sim,simthread = CompuCellSetup.getCoreSimulationObjects()
configureSimulation(sim)            

CompuCellSetup.initializeSimulationObjects(sim,simthread)
#this section calls the steppable classes
steppableRegistry=CompuCellSetup.getSteppableRegistry()

from SomiteMechModel_3XXSteppables import initializer
cleftins=initializer(sim,1,wall_w,Nx,Ny,lambda_v,Necto,ecto_wd,ecto_ht,pB,pA,pL,leng_dm1,bre_dm1)
steppableRegistry.registerSteppable(cleftins)

from SomiteMechModel_3XXSteppables import linkadder
cp=linkadder(sim,1,LamFP_c,LamFP_j,max_lambda)
steppableRegistry.registerSteppable(cp)

from SomiteMechModel_3XXSteppables import signal_constrict
sp=signal_constrict(sim,1,relax_time,wave_speed)
steppableRegistry.registerSteppable(sp)

from SomiteMechModel_3XXSteppables import constrict
cc=constrict(sim,1,bre_dm1,leng_dm1,LamFP_j,rate,Nset,relax_time,wave_speed,max_lambda,cutoff)
steppableRegistry.registerSteppable(cc)

CompuCellSetup.mainLoop(sim,simthread,steppableRegistry)


