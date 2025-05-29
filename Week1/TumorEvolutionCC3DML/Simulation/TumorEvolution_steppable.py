
from PySteppables import *
import CompuCell
import sys
from PySteppablesExamples import MitosisSteppableBase
import random
from math import *
from PlayerPython import *
from copy import deepcopy
import os
import numpy as np

import time

import os.path

def getCellCOMPoint3D(cell):
    pt=CompuCell.Point3D()
    pt.x=int(round(cell.xCOM))
    pt.y=int(round(cell.yCOM))
    pt.z=int(round(cell.zCOM))
    
    return pt
        
class GrowthSteppable(SteppableBasePy):
    def __init__(self,_simulator,_frequency):
        SteppableBasePy.__init__(self,_simulator,_frequency)        
        self.parameters=None
        
    def initParameters (self, _parameters):
        self.parameters=deepcopy(_parameters)
    
    def start(self):
        ip=self.parameters
        
        for cell in self.cellList:
            cell.targetVolume=ip.V0
            cell.lambdaVolume=ip.LBD_V0
            cell.targetSurface=ip.S0
            cell.lambdaSurface=ip.LBD_S0
            cellDict=CompuCell.getPyAttrib(cell)
            cellDict["Counter"]=0            
            cellDict["Health"]=0
            cellDict["Starv"]=0
        
    def step(self,mcs):    
        ip=self.parameters
        if mcs < ip.MCSThr:
            return
            
        
        glucoseField=CompuCell.getConcentrationField(self.simulator,'Glucose')
        
        if not len(self.cellList):
            self.stopSimulation()
            
            
        
        for cell in self.cellList:
            pt=getCellCOMPoint3D(cell)                                
            conc=glucoseField.get(pt)                
            cellDict=CompuCell.getPyAttrib(cell)
            
            #Necrotic Cells shrinkage
            if cell.type == self.NECROTIC:
                cell.targetVolume-=min(ip.decvol,cell.targetVolume)                    
                cell.targetSurface=ip.ktgs*sqrt(cell.targetVolume)

            #Proliferating Cancer Cells growth
            if cell.type == self.PCANCER:                                                            
                cell.targetVolume+=ip.incvol*max(0,conc - ip.PGrThr0)
                cell.targetSurface=ip.ktgs*sqrt(cell.targetVolume)
                
            #Stem Cells
            if cell.type == self.PSTEM:                    
                cell.targetVolume+=ip.incvol*max(0,conc - ip.SGrThr0)
                cell.targetSurface=ip.ktgs*sqrt(cell.targetVolume)


class TypeTransitionSteppable(SecretionBasePy): # SecretionBasePy inherits from SteppableBasePy
    def __init__(self,_simulator,_frequency):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        SecretionBasePy.__init__(self,_simulator, _frequency)
        self.parameters=None
        
    def initParameters (self, _parameters):
        self.parameters=deepcopy(_parameters)
    
    def step(self,mcs):
        ip=self.parameters        
        
        if mcs<ip.MCSThr:
            return 
            
        
        for cell in self.cellList:
        
            cellDict=CompuCell.getPyAttrib(cell)
            
            #Proliferating -> Necrotic
            if cell.type == self.PCANCER:
                if cellDict["Starv"] > ip.PNeThr0:
                    cell.type=self.NECROTIC
                    cellDict["Health"]=0
                    
            #Quiescent -> Necrotic
            #Quiescent -> PCANCER                
            if cell.type==self.QCANCER:                
                if cellDict["Starv"] > ip.QNeThr0:
                    cell.type=self.NECROTIC
                    cellDict["Health"]=0
                if cellDict["Health"] > ip.QPThr0:
                    cell.type=self.PCANCER
                    cellDict["Health"]=0

            # Stem -> Necrotic
            if cell.type == self.PSTEM:
                if cellDict["Starv"] > ip.SNeThr0:
                    cell.type=self.NECROTIC
                    cellDict["Health"]=0

            #Quiescent Stem -> Necrotic
            #Quiescent Stem -> Stem
            if cell.type == self.QSTEM:                
                if cellDict["Starv"] > ip.QSNeThr0:
                    cell.type=self.NECROTIC
                    cellDict["Health"]=0
                if cellDict["Health"] > ip.QSSThr0:
                    cell.type=self.PSTEM
                    cellDict["Health"]=0
                            
class MitosisSteppable(MitosisSteppableBase):
    def __init__(self,_simulator,_frequency):
        MitosisSteppableBase.__init__(self,_simulator, _frequency)
        self.adhesionFlexPlugin=CompuCell.getAdhesionFlexPlugin()
                
    def initParameters (self, _parameters):

        self.parameters=deepcopy(_parameters)
        
    def start(self):
        ip=self.parameters
        
        for cell in self.cellList:
            if cell:
                cellDict=CompuCell.getPyAttrib(cell)
                cellDict["Counter"]=0 # Number of divisions	

    def step(self,mcs):
        ip=self.parameters
                
        cells_to_divide=[]
        for cell in self.cellList:
            if ((cell.type==self.PCANCER or cell.type==self.QCANCER) and cell.volume>ip.volmaxmit) or ((cell.type==self.PSTEM or cell.type==self.QSTEM) and cell.volume>ip.Svolmaxmit):
                cells_to_divide.append(cell)

        for cell in cells_to_divide:           
            self.divideCellRandomOrientation(cell)

    def updateAttributes(self):
        ip=self.parameters
        parentCell=self.mitosisSteppable.parentCell
        childCell=self.mitosisSteppable.childCell
        parentCell.targetVolume=ip.V0
        childCell.targetVolume=ip.V0
        parentCell.targetSurface=ip.ktgs*sqrt(parentCell.targetVolume)
        childCell.targetSurface=ip.ktgs*sqrt(childCell.targetVolume)
        parentCell.lambdaVolume=ip.LBD_V0
        parentCell.lambdaSurface=ip.LBD_S0
        childCell.lambdaVolume=ip.LBD_V0
        childCell.lambdaSurface=ip.LBD_S0

        parentCellDict=CompuCell.getPyAttrib(parentCell)
        childCellDict=CompuCell.getPyAttrib(childCell)

        if parentCell.type == self.PCANCER:
        
            temp=random.gauss(ip.maxdiv,2)
            if  parentCellDict["Counter"] <= temp  :
                parentCell.type=self.QCANCER            # both cells are Q after mitosis
                childCell.type=self.QCANCER
                parentCellDict["Counter"]+=1
                
            childCellDict["Counter"]=deepcopy(parentCellDict["Counter"])
            
            if parentCellDict["Counter"] > temp :
                parentCell.type=self.NECROTIC
                childCell.type=self.NECROTIC

        if parentCell.type == self.PSTEM or parentCell.type == self.QSTEM :# Stem cell
            parentCellDict["Counter"]+=1			
            parentCell.type=self.QSTEM                                       # One is QS and
            childCell.type=self.QCANCER                                         # the other is QC
            
            if random.random() <= ip.probstem:         # But there is a chance for a 2nd QS 
                childCell.type=self.QSTEM
            childCellDict["Counter"]=0
            
        parentCellDict["Starv"]=0
        childCellDict["Starv"]=0
        parentCellDict["Health"]=0
        childCellDict["Health"]=0

        #getting actual Cadh and Int values
        jcadh=self.adhesionFlexPlugin.getAdhesionMoleculeDensityByIndex(parentCell,0)
        jint=self.adhesionFlexPlugin.getAdhesionMoleculeDensityByIndex(parentCell,1)
        jFN=self.adhesionFlexPlugin.getAdhesionMoleculeDensityByIndex(parentCell,2)
        
        #probability for mutation
        if parentCell.type != self.NECROTIC:
            r=random.random()
            if r < ip.probmut:
                new_cadh=random.gauss(jcadh,ip.cadhstdev)
                    
                if new_cadh >= 0 and new_cadh <= 16:
                    jcadh=new_cadh
                                    
            r=random.random()
            
            if r < ip.probmut:
                new_int=random.gauss(jint,ip.cadhstdev)
                if new_int >= 0 and new_int <= 16:
                    jint=new_int
                    
        # setting new adhesion density for product cell
        self.adhesionFlexPlugin.assignNewAdhesionMoleculeDensityVector(parentCell,[jcadh,jint,jFN])
        self.adhesionFlexPlugin.assignNewAdhesionMoleculeDensityVector(childCell,[jcadh,jint,jFN])

# calculates the rates of starvations - StarvationDamageAcumulator       
class StarvationDamageAcumulator(SteppableBasePy): 
    def __init__(self,_simulator,_frequency):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        
    def initParameters (self, _parameters):
        self.parameters=deepcopy(_parameters)
        
    def start(self):
        for cell in self.cellList:
            cellDict=CompuCell.getPyAttrib(cell)
            cellDict["Starv"]=0
            cellDict["Health"]=0

    def MM(self,x,m,k):
        return (m*x/(x + k))
        			
    def step(self,mcs):
        
        ip=self.parameters        
        glucoseField=CompuCell.getConcentrationField(self.simulator,'Glucose')

        if mcs>ip.MCSThr: 
          for cell in self.cellList:

            if cell.type != self.NECROTIC:               
                cellDict=CompuCell.getPyAttrib(cell)
                
                pt=getCellCOMPoint3D(cell)                
                
                conc=glucoseField.get(pt)
                
                if cell.type == self.PCANCER:
                    if conc < ip.GluD :    
                        cellDict["Starv"]+=abs(self.MM(conc,ip.PUgMax,ip.GluK) - self.MM(ip.GluD,ip.PUgMax,ip.GluK))
                    else:
                        cellDict["Health"]+=self.MM(conc,ip.PUgMax,ip.GluK) - self.MM(ip.GluD,ip.PUgMax,ip.GluK) 
                        
                if cell.type == self.QCANCER:
                    if conc< ip.GluD:
                        cellDict["Starv"]+=abs(self.MM(conc,ip.QUgMax,ip.GluK) - self.MM(ip.GluD,ip.QUgMax,ip.GluK)) 
                    else:
                        cellDict["Health"]+=self.MM(conc,ip.QUgMax,ip.GluK) - self.MM(ip.GluD,ip.QUgMax,ip.GluK) 
                if cell.type == self.PSTEM :
                    if conc < ip.GluD:
                        cellDict["Starv"]+=abs(self.MM(conc,ip.SUgMax,ip.GluK) - self.MM(ip.GluD,ip.SUgMax,ip.GluK))
                    else:
                        cellDict["Health"]+=self.MM(conc,ip.SUgMax,ip.GluK) - self.MM(ip.GluD,ip.SUgMax,ip.GluK) 
                        
                if cell.type == self.QSTEM:
                    if conc< ip.GluD:
                        cellDict["Starv"]+=abs(self.MM(conc,ip.QSUgMax,ip.GluK) - self.MM(ip.GluD,ip.QSUgMax,ip.GluK))
                    else:
                        cellDict["Health"]+=self.MM(conc,ip.QSUgMax,ip.GluK) - self.MM(ip.GluD,ip.QSUgMax,ip.GluK) 
                        
from PySteppables import *
import CompuCell
import sys

from PlayerPython import *
import CompuCellSetup
from math import *


class DataOutput(SteppableBasePy):
    def __init__(self,_simulator,_frequency=1000):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        self.outStr=''
        
    def initParameters (self, _parameters):
        self.parameters=deepcopy(_parameters)   
        
    def writeParameters(self):
        fileName='Parameters.dat'
        try:                
            fileHandle,fullFileName=self.openFileInSimulationOutputDirectory(fileName,"w")
        except IOError:
            print "Could not open file ", "YOUR FILE NAME"," for writing. "                
            return

        headerStr=''
        valueStr=''
        for name,value  in self.parameters.__dict__.iteritems():
            headerStr+=name+','
            valueStr+=str(value)+','
        
        print >>fileHandle,headerStr[:len(headerStr)-1]
        print >>fileHandle,valueStr[:len(valueStr)-1]        


    def start(self):
        self.writeParameters()
        pass
        
    def step(self,mcs):
        
        
        fileName='Data_'+str(mcs)+'.dat'

        try:                
            fileHandle,fullFileName=self.openFileInSimulationOutputDirectory(fileName,"w")
        except IOError:
            print "Could not open file ", "YOUR FILE NAME"," for writing. "                
            return
            
        print >> fileHandle,'id,type,typename,vol,sur,cad,int,fn,xcom,ycom'

#         from functools import partial
#         mapfunc = partial(p_out, _arg=20.2)        
        
        def p_out(x):
#             print >> fileHandle,str(x),",",
            self.outStr+=str(x)+","

        
        
        
     
        for cell in self.cellList:

            jcadh=self.adhesionFlexPlugin.getAdhesionMoleculeDensityByIndex(cell,0)
            jint=self.adhesionFlexPlugin.getAdhesionMoleculeDensityByIndex(cell,1)
            jFN=self.adhesionFlexPlugin.getAdhesionMoleculeDensityByIndex(cell,2)            
            data_list=[cell.id,cell.type,self.potts.getAutomaton().getTypeName(cell.type),cell.volume,cell.surface,jcadh,jint,jFN,cell.xCOM,cell.yCOM]
     
                
            self.outStr = ''     

            map (p_out, data_list)
            print >> fileHandle,self.outStr[:len(self.outStr)-1]
#             print 'outStr=',self.outStr

        fileHandle.close()
            
    def finish(self):
        # this function may be called at the end of simulation - used very infrequently though
        return
    
