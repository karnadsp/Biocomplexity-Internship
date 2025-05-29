import CompuCellSetup
# DermisMaturationSteppables.py

from PySteppables import *
import CompuCell
import sys

# from PySteppablesExamples import MitosisSteppableBase
from PySteppablesExamples import *

       
import random
from math import *
from PlayerPython import *
from copy import deepcopy
import os, inspect
import numpy as np

import time

import os.path

from XMLUtils import dictionaryToMapStrStr as d2mss
from XMLUtils import CC3DXMLListPy 


def getCellCOMPoint3D(cell):
    pt=CompuCell.Point3D()
    pt.x=int(round(cell.xCOM))
    pt.y=int(round(cell.yCOM))
    pt.z=int(round(cell.zCOM))
    
    return pt
     


class ConstraintInitializerSteppable(SteppableBasePy):
    
    def __init__(self,simulator,frequency,cd,targV,LamV):
        SteppableBasePy.__init__(self,simulator,frequency)
        self.cd=cd;                   
        self.targV=targV;           
        self.LamV=LamV;

        self.growth=0.2*cd

    def start(self):
        #Drawing Tube
        Lx3=int(floor(self.dim.x/2));    
        Ly3=int(floor(self.dim.y/2));
        dAng=2.*pi/10.;         #there are 10 cell inside the tubule in each xy-plane      
        AngPlus=0.;
        
        AngPlusEpi=0.;
        dAngEpi=2.*pi/50.;         #there are 100 cell in the perimeter of the tubule in each xy-plane      

        Rm=10.*self.cd/(2.*pi)  #Mean lumen diameter ~1.6 cell diameter         
        Rmin=Rm-self.cd/2.;                 
        Rmax=Rm+self.cd/2;
        lumen=self.newCell(self.LUMEN);
        
        for z in range(self.dim.z):
            if (z % self.cd == 0):
                #Creating new cells PROGENITORS
                c=[]; 
                for i in range(10):
                    c.append(self.newCell(self.PROGENITORS))
                
                
                #Creating new cells EPIDERMIS
                e=[]; 
                for i in range(50):
                    e.append(self.newCell(self.EPIDERMIS))
                
                AngPlus+=pi/10.
                AngPlusEpi+=pi/50.
            
            #Drawing
            for x in range(self.dim.x):
                dx=x-Lx3
                for y in range(self.dim.y):
                    dy=y-Ly3;
                    R=sqrt(dx*dx+dy*dy)
                    if(R<=Rmin): # create lumen
                        self.cellField[x,y,z]=lumen
                    elif(R<=Rmax):  # create progenitors
                        ang=acos(dx/R)
                        if(dy<0): ang=2.*pi-ang;
                        ang=(ang+AngPlus)%(2.*pi)
                        a=int(floor(ang/dAng))
                        if (a==10): cell=c[0];
                        else: cell=c[a];
                        self.cellField[x,y,z]=cell
                    elif(R>Rmax and R<=(Rmax+0.2*Rmax)):  # create epidermis
                        ang=acos(dx/R)
                        if(dy<0): ang=2.*pi-ang;
                        ang=(ang+AngPlusEpi)%(2.*pi)
                        a=int(floor(ang/dAngEpi))
                        if (a==50): cell=c[0];
                        else: cell=e[a];
                        self.cellField[x,y,z]=cell
        
        #Setting volume parameters
        for cell in self.cellList:
            
            if cell.type == self.EPIDERMIS:
                cell.lambdaVolume = 5.*self.LamV
                cell.targetVolume=1.*cell.volume

            elif cell.type == self.ECM:
                cell.lambdaVolume = 5.*self.LamV
                cell.targetVolume=cell.volume

            elif cell.type == self.LUMEN:
                cell.lambdaVolume = 5.*self.LamV
                cell.targetVolume=cell.volume
            
            else: #(not (cell.type==self.LUMEN)):
                cell.lambdaVolume=self.LamV
            
                if cell.type==self.ADIPOCYTES:
                    cell.targetVolume=10.*self.targV
                else:
                    cell.targetVolume=cell.volume
                    

class GrowthSteppable(SteppableBasePy):
    def __init__(self,_simulator,_frequency=1):
        SteppableBasePy.__init__(self,_simulator,_frequency)
    
    def step(self,mcs):
        fieldEGF=CompuCell.getConcentrationField(self.simulator,"EpidermalGrowthSignal")
        maxValEGF=fieldEGF.max()
        
        pt=CompuCell.Point3D()
        
        print('MCS=',mcs) 
        
        if mcs > 100:
            for cell in self.cellListByType(self.EPIDERMIS):
                a = 1
                for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):                
                    if not neighbor:
                        a = 0
                        break
                if a:
                    cell.type = self.ECM 
                    cell.targetVolume = 1
                    cell.lambdaVolume = 100 
            
        for cell in self.cellListByType(self.PROGENITORS):
            cell.targetVolume+=1
            for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):                
                if not neighbor:
                    cell.type = self.EPIDERMIS
                    cell.targetVolume = 100
                    cell.lambdaVolume = 100
                    break
        
#         for cell in self.cellListByType(self.PPAP):
#             for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):
#                 if not neighbor:
#                     cell.type = self.EPIDERMIS
#                     cell.targetVolume = 100
#                     cell.lambdaVolume = 100
#                     break
                 
        for cell in self.cellListByType(self.PPAP, self.PRET):
            pt.x=int(cell.xCOM)
            pt.y=int(cell.yCOM)
            pt.z=int(cell.zCOM)
            concentrationAtCOM_EGF=fieldEGF.get(pt)
            
            if concentrationAtCOM_EGF>(maxValEGF/10):
                cell.targetVolume+=.4
            else:
                cell.targetVolume+=.1
            
        for cell in self.cellListByType(self.ADIPOCYTES,self.FATTY):
            a = 0
            for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):                
                if neighbor and neighbor.type == self.LUMEN:
                    pass
                else:
                    a = 1
                    break
            if a == 0:
                cell.type = self.LUMEN
                cell.targetVolume = 0
                cell.lambdaVolume = 100  
                
            if mcs < 1000 and cell.volume<100:
                cell.targetVolume+=1
 
        
class TransitionSteppable(SteppableBasePy):
    def __init__(self,_simulator,_frequency=1):
        SteppableBasePy.__init__(self,_simulator,_frequency)
    
    def step(self,mcs):
        fieldEGF=CompuCell.getConcentrationField(self.simulator,"EpidermalGrowthSignal")
        maxValEGF=fieldEGF.max()
        
        pt=CompuCell.Point3D()
        switchT = .5 # changed from .1
        switchTb = .01
        
        # proliferative cells become quiescent        
        for cell in self.cellListByType(self.PPAP,self.PRET):
            pt.x=int(cell.xCOM)
            pt.y=int(cell.yCOM)
            pt.z=int(cell.zCOM)
            concsEGF=fieldEGF.get(pt)
            
            if concsEGF < 50:
                s = 1e-6
                sECM = 0.0
                
                for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):  
                    s+= commonSurfaceArea              
                    if neighbor and (neighbor.type in [self.ECM, self.LUMEN, self.QRET, self.QPAP, self.ADIPOCYTES]):
                        sECM += commonSurfaceArea

                if sECM/s > switchT:
                    if cell.type==self.PPAP:
                        cell.type=self.QRET
                    elif cell.type==self.PRET:
                        cell.type=self.QPAP
           
#         # quiescent cells re-start proliferating
#         for cell in self.cellListByType(self.QRET, self.QPAP):
#             s = 1e-6
#             sECM = 0.0
            
#             for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):  
#                 s+= commonSurfaceArea              
#                 if neighbor and neighbor.type == self.ECM:
#                     sECM += commonSurfaceArea

#             if sECM/s <= switchTb:
#                 if cell.type==self.QRET:
#                     cell.type=self.PPAP
#                 elif cell.type==self.QPAP:
#                     cell.type=self.PRET

                
class AdipocytesMaturationSteppable(SteppableBasePy):    

    def __init__(self,_simulator,_frequency=1):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        
    def step(self,mcs): 
        
        if mcs>300*self.frequency:
        
            a = 0
            for cell in self.cellListByType(self.QRET,self.QPAP,self.QMYOF):
                
                cellDict=CompuCell.getPyAttrib(cell);
                for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):
                    if a < 5:
                        if (neighbor and (neighbor.type == self.LUMEN)):
                            if cell.type == self.QRET:
                                cell.type=self.ADIPOCYTES
                            else:
                                cell.type = self.FATTY
                            a+= 1
                    

class MitosisSteppable(MitosisSteppableBase):
    def __init__(self,_simulator,_frequency=1):
        MitosisSteppableBase.__init__(self,_simulator, _frequency)
            
    def start(self):
        for cell in self.cellList:#ByType(self.PROGENITORS,self.PPAP,self.PRET):
            cellDict=CompuCell.getPyAttrib(cell)
            cellDict["DivisionCounter"]=0 # Number of cell divisions
    
    def step(self,mcs):
        field=CompuCell.getConcentrationField(self.simulator,"EpidermalGrowthSignal")
        maxVal=field.max()
        
        fieldWH=CompuCell.getConcentrationField(self.simulator,"WoundHealingSignal")
        
        pt=CompuCell.Point3D()
        cells_to_divide=[]
        
        for cell in self.cellListByType(self.PROGENITORS):
            if cell.volume>50:
                cells_to_divide.append(cell)
                cellDict=CompuCell.getPyAttrib(cell)
                cellDict["DivisionCounter"]+=1
    
        for cell in self.cellListByType(self.PPAP,self.PRET):
            if cell.volume>50:
                pt.x=int(cell.xCOM)
                pt.y=int(cell.yCOM)
                pt.z=int(cell.zCOM)
                concentrationAtCOM=field.get(pt)
                if concentrationAtCOM>.5*maxVal:
                    cells_to_divide.append(cell)
                    cellDict=CompuCell.getPyAttrib(cell)
                    cellDict["DivisionCounter"]+=1

        for cell in self.cellListByType(self.EPIDERMIS):
            if cell.volume>100:
                cells_to_divide.append(cell)

        for cell in self.cellListByType(self.MYOF):
            if cell.volume>50:
                pt.x=int(cell.xCOM)
                pt.y=int(cell.yCOM)
                pt.z=int(cell.zCOM)
                concentrationAtCOM=fieldWH.get(pt)
                if concentrationAtCOM>10:# and cellDict["DivisionCounter"]<10:
                    cells_to_divide.append(cell)

        for cell in cells_to_divide:
            self.divideCellRandomOrientation(cell)
    

    def updateAttributes(self):
        self.mitosisSteppable.parentCell.targetVolume = 50.0 # reducing parent target volume
        self.cloneParent2Child()            
        
        # for more control of what gets copied from parent to child use cloneAttributes function
        # self.cloneAttributes(sourceCell=self.parentCell, targetCell=self.childCell, no_clone_key_dict_list = [attrib1, attrib2] )
        
        if self.mitosisSteppable.parentCell.type==self.PROGENITORS:
            cellDict=CompuCell.getPyAttrib(self.mitosisSteppable.parentCell)
                
            if cellDict["DivisionCounter"]<10: #changed from 10
                self.mitosisSteppable.childCell.type = self.PROGENITORS
                cellDict["DivisionCounter"]+=1

            elif cellDict["DivisionCounter"]>=5:
                self.mitosisSteppable.parentCell.type = self.PPAP
                self.mitosisSteppable.childCell.type = self.PPAP
        
        
        elif self.mitosisSteppable.parentCell.type==self.PPAP:
            self.mitosisSteppable.childCell.type = self.PPAP
        
        elif self.mitosisSteppable.parentCell.type==self.PRET:
            self.mitosisSteppable.childCell.type = self.PPAP

        elif self.mitosisSteppable.parentCell.type==self.MYOF:
            self.mitosisSteppable.childCell.type = self.MYOF

        
####################################################################################


class ECMSteppable(MitosisSteppableBase):
    def __init__(self,_simulator,_frequency=1):
        MitosisSteppableBase.__init__(self,_simulator,_frequency)

    def initParameters (self, _parameters):
        self.parameters=deepcopy(_parameters)
            
    def step(self,mcs):
            
        fieldEGF=CompuCell.getConcentrationField(self.simulator,"EpidermalGrowthSignal")
        maxValEGF=fieldEGF.max()
        
        pt=CompuCell.Point3D()
      
        cells_to_produce_ECM=[]
        cells_to_produce_ECM_qui=[]
        cells_to_produce_ECM_prol=[]
        
        for cell in self.cellListByType(self.QRET,self.QPAP,self.QMYOF):
            cells_to_produce_ECM_qui.append(cell)
                    
        for cell in self.cellListByType(self.PRET,self.PPAP,self.MYOF):
            pt.x=int(cell.xCOM)
            pt.y=int(cell.yCOM)
            pt.z=int(cell.zCOM)
            concsEGF=fieldEGF.get(pt)
            if concsEGF < 100:
                cells_to_produce_ECM_prol.append(cell)
        
        nbLUMEN = 0.
        # calculate all cells volume    
        for cell in self.cellListByType(self.LUMEN):
            nbLUMEN += cell.volume
        nbECM = 0.
        # calculate ECM volume       
        for cell in self.cellListByType(self.ECM): 
            nbECM += cell.volume
        nbTOTAL2 = 0.
        # calculate all cells volume    
        for cell in self.cellList:
            nbTOTAL2 += cell.volume
        nbTOTAL2 = nbTOTAL2 - nbLUMEN
        
        prob_q = .3 + nbECM/nbTOTAL2
#         if mcs > 350:
#             prob_q += nbECM/nbTOTAL2
        
        prob_p = 0.1  #changed from .09
        nq = int(prob_q*len(cells_to_produce_ECM_qui)+.5)
        np = int(prob_p*len(cells_to_produce_ECM_prol)+.5)
        
        if nq<1:
            for cell in cells_to_produce_ECM_qui:
                if random.random()<prob_q:
                    self.divideCellRandomOrientation(cell)
        else:
            for i in range(nq):
                cell = random.choice(cells_to_produce_ECM_qui)
                
#                 cell = cells_to_produce_ECM_qui[i]
                self.divideCellRandomOrientation(cell)
        
        if np<1:
            for cell in cells_to_produce_ECM_prol:
                if random.random()<prob_p:
                    self.divideCellRandomOrientation(cell)
        else:
            for j in range(np):
                cell = random.choice(cells_to_produce_ECM_prol)
                
#                 cell = cells_to_produce_ECM_prol[j]
                self.divideCellRandomOrientation(cell)


    def updateAttributes(self):
        
        if self.mitosisSteppable.parentCell.type in [self.QRET,self.QPAP]:
            self.mitosisSteppable.parentCell.targetVolume = 50 # keeping parent target volume
            self.mitosisSteppable.parentCell.lamdaVolume = 100 # set large lambda volume
            
            self.mitosisSteppable.childCell.type = self.ECM
            self.mitosisSteppable.childCell.targetVolume = 20  # set higher volume for ECM from quiescent
            self.mitosisSteppable.childCell.lamdaVolume = 5.*50  # set large lambda volume
        
        elif self.mitosisSteppable.parentCell.type in [self.PPAP,self.PRET]:
            self.mitosisSteppable.parentCell.targetVolume = 50 # keeping parent target volume

            self.mitosisSteppable.childCell.type = self.ECM
            self.mitosisSteppable.childCell.targetVolume = 20  # set smaller volume for ECM from proliferative
            self.mitosisSteppable.childCell.lamdaVolume = 5.*50  # set large lambda volume
            
        elif self.mitosisSteppable.parentCell.type==self.MYOF:
            self.mitosisSteppable.parentCell.targetVolume = 50 # keeping parent target volume
            
            self.mitosisSteppable.childCell.type = self.ECM
            self.mitosisSteppable.childCell.targetVolume = 2  # set smaller volume for ECM from proliferative             
            self.mitosisSteppable.childCell.lamdaVolume = 5.*50  # set large lambda volume 
        
        elif self.mitosisSteppable.parentCell.type==self.QMYOF:
            self.mitosisSteppable.parentCell.targetVolume = 50 # keeping parent target volume
            self.mitosisSteppable.parentCell.lamdaVolume = 100  # set large lambda volume
            
            self.mitosisSteppable.childCell.type = self.ECM
            self.mitosisSteppable.childCell.targetVolume = 2  # set smaller volume for ECM from quiescent             
            self.mitosisSteppable.childCell.lamdaVolume = 5.*50  # set large lambda volume



class LumenFlux(SteppableBasePy): # NEW flux based lumen growth
    def __init__(self,simulator,frequency,LamV,Kl,ApArea):
        SteppableBasePy.__init__(self,simulator,frequency)
        self.boundaryStrategy=CompuCell.BoundaryStrategy.getInstance()
        self.maxNeighborIndex=self.boundaryStrategy.getMaxNeighborIndexFromNeighborOrder(1)
        self.LamV=LamV;   
        self.Kl=Kl;  
        self.ApArea=ApArea;
        
    def start(self):
        for cell in self.cellListByType(self.LUMEN):
            self.LumenID=cell.id
            self.LumenVol=cell.volume
            cell.lambdaVolume=10*self.LamV
            cell.targetVolume=self.LumenVol

    def Merging(self,cell,cellD):
        L=[]; pixelList=CellPixelList(self.pixelTrackerPlugin,cellD);
        for pixelData in pixelList:
            L.append(CompuCell.Point3D(pixelData.pixel))
        cell.targetVolume+=cellD.targetVolume
        for pt in L:
            self.cellField.set(pt,cell)
        self.cleanDeadCells()
        
    def step(self,mcs):
        #LUMEN MAINTENANCE
        List=[];
        dCell=[];
        for cell in self.cellListByType(self.LUMEN):  #Lumen cells
            sApical=0
            nCell=0
            for neighbor, commonSurfaceArea in self.getCellNeighborDataList(cell):
                if (not neighbor):  #Lumen-Medium
                    cell.targetVolume-=commonSurfaceArea
                
                elif (neighbor and (neighbor.type == self.LUMEN)): #break
                    if (cell.id < neighbor.id):
                        if ((neighbor.id not in dCell) and (cell.id not in dCell)):
                            List.append([cell,neighbor])
                            dCell.append(neighbor.id)
                
                elif (neighbor and neighbor.type in [self.ADIPOCYTES,self.QRET,self.QPAP,self.FATTY,self.PPAP,self.PRET]):
                    sApical+=commonSurfaceArea
                    nCell+=1
                
                elif (neighbor and neighbor.type == self.QRET):
                    sApical+=commonSurfaceArea
                    nCell+=1
            
#             cell.targetVolume+=.9*self.Kl*(nCell-sApical/(self.ApArea))
            
            if mcs<400:
                if cell.targetVolume > 0:
                    cell.targetVolume+=1.2*self.Kl*(nCell-sApical/(self.ApArea))
            
            elif mcs<1200:
                if cell.targetVolume > 0:
                    cell.targetVolume+=1.1*self.Kl*(nCell-sApical/(self.ApArea))
            else:
                cell.targetVolume+=1*self.Kl*(nCell-sApical/(self.ApArea))
#                 cell.targetVolume=cell.volume


class PlotCells(SteppableBasePy):
    
    def __init__(self,_simulator,_frequency=1):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        self.pW1 = None
        self.pW2 = None
        
    def initialize_plots(self):
        if self.pW1:# or self.PW2:
            return
        
#         self.pW=self.addNewPlotWindow(_title='Dermal Maturation',_xAxisTitle='MonteCarlo Step (MCS)',_yAxisTitle='Nb cells', _xScaleType='linear',_yScaleType='linear')
#         self.pW.addPlot('Progenitors',_style='Lines',_color='blue',_size=3)
#         self.pW.addPlot('Papillary',_style='Lines',_color='red',_size=3)
#         self.pW.addPlot('Reticular',_style='Lines',_color='magenta',_size=3)
#         self.pW.addPlot('Adipocytes',_style='Lines',_color='navy',_size=3)
#         self.pW.addPlot('Total Cell Number',_style='Lines',_color='gold',_size=3)
#         self.pW.addPlot('ECM Density',_style='Lines',_color='pale turquoise',_size=3)
        
        self.pW1=self.addNewPlotWindow(_title='Dermal Maturation',_xAxisTitle='MonteCarlo Step (MCS)',_yAxisTitle='Nb cells', _xScaleType='linear',_yScaleType='linear')
        self.pW1.addPlot('Proliferative cells',_style='Lines',_color='blue',_size=3)
        self.pW1.addPlot('ECM',_style='Lines',_color='green',_size=3)
#         self.pW1.addPlot('Total Cell Number',_style='Lines',_color='gold',_size=3)
        
        self.pW2=self.addNewPlotWindow(_title='Lineages evolution',_xAxisTitle='MonteCarlo Step (MCS)',_yAxisTitle='Nb cells', _xScaleType='linear',_yScaleType='linear')
#         self.pW2.addPlot('MF',_style='Lines',_color='tomato',_size=3)
        self.pW2.addPlot('PF',_style='Lines',_color='royalblue',_size=3)
        self.pW2.addPlot('QF',_style='Lines',_color='goldenrod',_size=3)
        self.pW2.addPlot('Adipocytes',_style='Lines',_color='saddlebrown',_size=3)
        self.pW2.addPlot('Myofibroblasts',_style='Lines',_color='violet',_size=3)
        
    def start(self):
#         self.pW=self.addNewPlotWindow(_title='Dermal Maturation',_xAxisTitle='MonteCarlo Step (MCS)',_yAxisTitle='Nb cells', _xScaleType='linear',_yScaleType='linear')
#         self.pW.addPlot('Progenitors',_style='Lines',_color='blue',_size=3)
#         self.pW.addPlot('Papillary',_style='Lines',_color='red',_size=3)
#         self.pW.addPlot('Reticular',_style='Lines',_color='magenta',_size=3)
#         self.pW.addPlot('Adipocytes',_style='Lines',_color='navy',_size=3)
#         self.pW.addPlot('Total Cell Number',_style='Lines',_color='gold',_size=3)
#         self.pW.addPlot('ECM Density',_style='Lines',_color='pale turquoise',_size=3)
        
        self.pW1=self.addNewPlotWindow(_title='Dermal Maturation',_xAxisTitle='MonteCarlo Step (MCS)',_yAxisTitle='Nb cells', _xScaleType='linear',_yScaleType='linear')
        self.pW1.addPlot('Proliferative cells',_style='Lines',_color='blue',_size=3)
        self.pW1.addPlot('ECM vol',_style='Lines',_color='green',_size=3)
        self.pW1.addPlot('ECM nb',_style='Lines',_color='gold',_size=3)
        
        self.pW2=self.addNewPlotWindow(_title='Lineages evolution',_xAxisTitle='MonteCarlo Step (MCS)',_yAxisTitle='Nb cells', _xScaleType='linear',_yScaleType='linear')
#         self.pW2.addPlot('MF',_style='Lines',_color='tomato',_size=3)
        self.pW2.addPlot('PF',_style='Lines',_color='royalblue',_size=3)
        self.pW2.addPlot('QF',_style='Lines',_color='goldenrod',_size=3)
        self.pW2.addPlot('Adipocytes',_style='Lines',_color='saddlebrown',_size=3)
        self.pW2.addPlot('Myofibroblasts',_style='Lines',_color='violet',_size=3)
        
#         self.initialize_plots()
 
        
            
        fileName='plots.txt'#+str(mcs)+'.csv'
        try:
            fileHandle,fullFileName\
            =self.openFileInSimulationOutputDirectory(fileName,"w")
        except IOError:
            print("Could not open file ", fileName," for writing. ")
            return
        print >>fileHandle, 'MCS','TotalCells','ProliferativeCells','ECM','MF','PF','QF','Adipocytes'
        fileHandle.close()
    
    def step(self,mcs):
        
        self.initialize_plots()
        
        nbQRET = len(self.cellListByType(self.QRET))
        nbPPAP = len(self.cellListByType(self.PPAP))
        nbPROG = len(self.cellListByType(self.PROGENITORS))
        nbADIPOCYTES = len(self.cellListByType(self.ADIPOCYTES))
        nbMYOF = len(self.cellListByType(self.MYOF))
        nbECM = len(self.cellListByType(self.ECM))
#         print "nbMYOF = ", nbMYOF
        nbTOTAL = float(nbQRET + nbPPAP + nbADIPOCYTES + nbPROG)
        nbTOTAL2 = float(nbTOTAL+nbECM)
        nbPROLIF = float(nbPROG + nbPPAP)
#         /float(nbQRET + nbPPAP + nbADIPOCYTES + nbPROG)
        volLUMEN = 0.
        # calculate all cells volume    
        for cell in self.cellListByType(self.LUMEN):
            volLUMEN += cell.volume
        volECM = 0.
        # calculate ECM volume       
        for cell in self.cellListByType(self.ECM): 
            volECM += cell.volume
        volTOTAL2 = 0.
        # calculate all cells volume    
        for cell in self.cellList:
            volTOTAL2 += cell.volume
        volTOTAL2 = volTOTAL2 - volLUMEN
        
#         self.pW.addDataPoint("Progenitors",mcs,nbPROG) # arguments are (name of the data series, x, y)
#         self.pW.addDataPoint("Papillary",mcs,nbPPAP) # arguments are (name of the data series, x, y)
#         self.pW.addDataPoint("Reticular",mcs,nbQRET) # arguments are (name of the data series, x, y)
#         self.pW.addDataPoint("Adipocytes",mcs,nbADIPOCYTES) # arguments are (name of the data series, x, y)
#         self.pW.addDataPoint("Total Cell Number",mcs,nbTOTAL) # arguments are (name of the data series, x, y)
#         self.pW.addDataPoint("ECM Density",mcs,nbECM) # arguments are (name of the data series, x, y)
        
#         self.pW2.addDataPoint("MF",mcs,nbPROG) # arguments are (name of the data series, x, y)
        self.pW2.addDataPoint("PF",mcs,nbPPAP+nbPROG) # arguments are (name of the data series, x, y)
        self.pW2.addDataPoint("QF",mcs,nbQRET) # arguments are (name of the data series, x, y)
        self.pW2.addDataPoint("Adipocytes",mcs,nbADIPOCYTES) # arguments are (name of the data series, x, y)
        self.pW2.addDataPoint("Myofibroblasts",mcs,nbMYOF) # arguments are (name of the data series, x, y)
        self.pW1.addDataPoint("Proliferative cells",mcs,nbPROLIF/nbTOTAL) # arguments are (name of the data series, x, y)
        self.pW1.addDataPoint("ECM vol",mcs,volECM/volTOTAL2) # arguments are (name of the data series, x, y)
        self.pW1.addDataPoint("ECM nb",mcs,nbECM/nbTOTAL2) # arguments are (name of the data series, x, y)
        
        self.pW1.showAllPlots() 
        self.pW2.showAllPlots() 
        
            
        fileName='plots.txt'#+str(mcs)+'.txt'
        try:
            fileHandle,fullFileName\
            =self.openFileInSimulationOutputDirectory(fileName,"a")
        except IOError:
            print("Could not open file ", fileName," for writing. ")
            return
        print >>fileHandle, mcs,nbTOTAL,nbPROLIF,nbECM,nbPROG,nbPPAP,nbQRET,nbADIPOCYTES
        fileHandle.close()
        
        
        
#############################################################################################################################################################                               
###################################################################### wound & repair #######################################################################
#############################################################################################################################################################                               

class CutRegion(SteppableBasePy):    
    def __init__(self,_simulator,_frequency):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        
    def start(self):
        # any code in the start function runs before MCS=0
        pass
        
    def step(self,mcs):
#         if mcs==200:
#             self.cut(self.dim.x/2,self.dim.y/2,10,20)
#         el
#         if mcs==50:
#             self.cut(250,285,10,30)
#             raw_input("Wound made! Press Enter to continue...")
#         if mcs==100:
#             xLength = 50
#             yLength = 50
#             self.cut(250,300,xLength,yLength)
#         if mcs==405:
#             xLength = 30
#             yLength = 40
#             self.cut(self.dim.x/2,210,xLength,yLength)
        if mcs==1205:
            xLength = 30
            yLength = 50
            self.cut(250,380,xLength,yLength)

    def getLumen(self):
        xm = self.dim.x/2
        lumen = 0
        y = self.dim.y
        while lumen == 0:
            y-=1
            cell=self.cellField[xm,y,0]
            if cell and (cell.type == self.LUMEN):
                return y
                
    def getEpidermis(self):
        xm = self.dim.x/2
        epi = 0
        y = self.dim.y
        while epi == 0:
            y-=1
            cell=self.cellField[xm,y,0]
            if cell and (cell.type == self.EPIDERMIS):
                return y
                
    
# only cells cut            
    def cut(self,x0,y0,dx,dy):
        medium=CompuCell.getMediumCell() #get medium
        deleteCells = []
        
        xi=int(max(x0-dx/2,0))
        xf=int(min(x0+dx/2,self.dim.x))
#         yi=int(max(y0-dy/2,0))
#         yf=int(min(y0+dy/2,self.dim.y))
        yf = self.getEpidermis()+10
        yi = self.getLumen()+8
        ycut = self.getEpidermis()-(yf-yi)/5
#         self.field=self.getConcentrationField("WoundHealingSignal")
        
        for x in range(xi,xf):
            for y in range(yi,yf):
                for z in range(self.dim.z):
                
#                     cell=self.cellField[x,y,z]
#                     if cell:
#                         cell.targetVolume-=1      #decrease cell target volume by 1
#                         if (-1<cell.targetVolume<0): 
#                             deleteCells.append(cell)
#                     self.cellField[x,y,z]=medium  #replacing cell pixel by medium
                    
                    cell=self.cellField[x,y,z]
                    
                    # new version
                    if cell: 
                        if y > ycut:
                            cell.type = self.BC
                            cell.targetVolume = cell.volume
                            cell.lambdaVolume = 20
                        elif cell.type != self.ADIPOCYTES and cell.type != self.BC:
                            cell.type = self.IC
                            cell.targetVolume = cell.volume
                            cell.lambdaVolume = 20
                            
#                     self.field[x,y,z]=20
                        
                    
#                     # initial version
#                     if cell:
#                         cell.type=self.BC      #changing cell type to blood clot
# #                         if (-1<cell.targetVolume<0): 
# #                             deleteCells.append(cell)
# #                     self.cellField[x,y,z]=medium  #replacing cell pixel by medium
                    
#                     self.field[x,y,z]=20
                    
# #         for cell in deleteCells:  #making sure cells are deleted
# #             self.deleteCell(cell)         
        

# cells and chemical fields cut       
#     def cut(self,x0,y0,dx,dy):
#         #list all fields to be erased here
#         field_1=self.getConcentrationField("EpidermalGrowthSignal")
#         field_2=self.getConcentrationField("ECMSignal")
        
#         medium=CompuCell.getMediumCell() #get medium
#         deleteCells = []
        
#         xi=int(max(x0-dx/2,0))
#         xf=int(min(x0+dx/2,self.dim.x))
#         yi=int(max(y0-dy/2,0))
#         yf=int(min(y0+dy/2,self.dim.y))
        
#         for x in range(xi,xf):
#             for y in range(yi,yf):
#                 for z in range(self.dim.z):

#                     cell=self.cellField[x,y,z]
#                     if cell and cell.type!=self.LUMEN:
#                         cell.targetVolume-=1      #decrease cell target volume by 1
#                         if (-1<cell.targetVolume<0):
#                             deleteCells.append(cell)
                    
#                     if cell and cell.type!=self.LUMEN:
#                         self.cellField[x,y,z]=medium  #replacing cell pixel by medium
        
#                         field_1[x,y,z]=0 #call all fields here
#                         field_2[x,y,z]=0 #call all fields here

                    
#         for cell in deleteCells:  #making sure cells are deleted
#             self.deleteCell(cell)    
        


class woundHealing(SteppableBasePy):    
    def __init__(self,_simulator,_frequency):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        
    def start(self):
        for cell in self.cellListByType(self.PPAP, self.QRET):
            cell.dict["WHgrad"] = 0    

    def step(self,mcs):
        
        # epidermis growth in response to either direct contact with blood clot or WH gradient
        fieldWH=self.getConcentrationField("WoundHealingSignal")
        maxValWH=fieldWH.max()
        pt=CompuCell.Point3D()
        epiBC = [];
        for cell in self.cellListByType(self.BC):
            for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):                
                if neighbor and neighbor.type==self.EPIDERMIS:
                    if neighbor.id not in epiBC:
                        epiBC.append(neighbor.id)
        for cell in self.cellListByType(self.EPIDERMIS):
            if cell.id not in epiBC:
                pt.x=int(cell.xCOM)
                pt.y=int(cell.yCOM)
                pt.z=int(cell.zCOM)
                wh_value=fieldWH[pt.x,pt.y,pt.z]
                if wh_value > maxValWH*.25:
                    epiBC.append(cell.id)
        for id in epiBC:
            cell=self.attemptFetchingCellById(id)
            cell.targetVolume+=10


        # PPap, QRet conversion into MyoF in response to WH gradient
        for cell in self.cellListByType(self.PPAP,self.QRET):
            pt.x=int(cell.xCOM)
            pt.y=int(cell.yCOM)
            pt.z=int(cell.zCOM)
            
#             concentrationAtCOMECM=fieldWH.get(pt)
#             print 'field1=',concentrationAtCOMECM
            wh_value=fieldWH[pt.x,pt.y,pt.z]
#             print 'field2=',wh_value
            if "WHgrad" not in cell.dict.keys():
                cell.dict["WHgrad"] = 0   
            cell.dict["WHgrad"]+=wh_value
            if cell.dict["WHgrad"] > 100:
                cell.type = self.MYOF
                cell.targetVolume = cell.volume
                cell.lambdaVolume = 20
                
            
        # destruction of BC
        breakBC = 1
        for cell in self.cellListByType(self.BC):
            for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):                
                if neighbor and neighbor.type!=self.BC:
                    breakBC = 0
                    break

        if breakBC == 1:
            for cell in self.cellListByType(self.BC):
                self.deleteCell(cell)
            
        
        # destruction of IC&co            
        for cell in self.cellListByType(self.IC):
            a = 0
            for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):                
                if neighbor and (neighbor.type == self.MYOF):
                    cell.targetVolume-=.1
                if cell.targetVolume < .1:
                    cell.type = self.ECM
                    cell.targetVolume = 2
                    cell.lambdaVolume = 20
                    a = 1
                    break
                    
            if a == 0:
                cell.targetVolume-=.01
                if cell.targetVolume < .1:
                    cell.type = self.ECM
                    cell.targetVolume = 2
                    cell.lambdaVolume = 20 
                    
                    
            
#             if "breakIC" not in cell.dict.keys():
#                 cell.dict["breakIC"] = 0
#             for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):                
#                 if neighbor and (neighbor.type == self.MYOF): 
#                     cell.dict["breakIC"]+=1
#             if cell.dict["breakIC"] > 2:
#                 cell.type = self.ECM
#                 cell.targetVolume = 2
#                 cell.lambdaVolume = 20
            
        
        # destruction of ECM in the imediates surroundings of the IC&co  
        for cell in self.cellListByType(self.ECM):
            pt.x=int(cell.xCOM)
            pt.y=int(cell.yCOM)
            pt.z=int(cell.zCOM)
            wh_value=fieldWH[pt.x,pt.y,pt.z]
#             if "WHgrad" not in cell.dict.keys():
#                 cell.dict["WHgrad"] = 0   
#             cell.dict["WHgrad"]+=wh_value
#             if cell.dict["WHgrad"] > maxValWH*.5:
            if wh_value > 10:
                cell.type = self.MYOF
                cell.targetVolume = 5
                cell.lambdaVolume = 20
            
    
        # MyoF conversion into PPap, QRet
        a = 1
        for cell in self.cellListByType(self.MYOF):
            for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):                
                if neighbor and (neighbor.type == self.IC):
                    a = 0
                    break
            if a == 1:
                pt.x=int(cell.xCOM)
                pt.y=int(cell.yCOM)
                pt.z=int(cell.zCOM)
                wh_value=fieldWH[pt.x,pt.y,pt.z]
                if wh_value < 5:
                    cell.type = self.QMYOF
                    cell.targetVolume = cell.volume
                    cell.lambdaVolume = 20  
                
            
#             pt.x=int(cell.xCOM)
#             pt.y=int(cell.yCOM)
#             pt.z=int(cell.zCOM)
            
# #             concentrationAtCOMECM=fieldWH.get(pt)
# #             print 'field1=',concentrationAtCOMECM
#             wh_value=fieldWH[pt.x,pt.y,pt.z]
# #          
#             if wh_value < .25*maxValWH:
#                 cell.type = self.QRET
#                 cell.targetVolume = cell.volume
#                 cell.lambdaVolume = 20    
            
    
            





#############################################################################################################################################################                               


class SteadyStateDiffusionSteeringSteppable(SteppableBasePy):
    def __init__(self,_simulator,_frequency):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        self.simulator=_simulator
        
    def step(self, mcs):
        if mcs>100:
            flexDiffXMLData=self.simulator.getCC3DModuleData("Steppable","SteadyStateDiffusionSolver2D")
            
            if flexDiffXMLData:
            
                diffusionFieldsElementVec=CC3DXMLListPy(flexDiffXMLData.getElements("DiffusionField"))
                for diffusionFieldElement in diffusionFieldsElementVec:
                    if diffusionFieldElement.getFirstElement("DiffusionData").getFirstElement("FieldName").getText()=="EpidermalGrowthSignal":
#                         diffConstElement=diffusionFieldElement.getFirstElement("DiffusionData").getFirstElement("DiffusionConstant")
#                         diffConst=float(diffConstElement.getText())
#                         diffConst+=0.01
#                         diffConstElement.updateElementValue(str(diffConst))
                        secretionElement=diffusionFieldElement.getFirstElement("SecretionData").getFirstElement("Secretion",d2mss({"Type":"Epidermis"}))
                        secretionConst=float(secretionElement.getText())
                        if secretionConst>0.05:
                            secretionConst-=.04
                            secretionElement.updateElementValue(str(secretionConst))
                            
                        else: 
                            self.frequency = 1000000
                            
                            
                # finally call simulator.updateCC3DModule(fiexDiffXMLData) to tell simulator to update model parameters - this is actual steering                            
                self.simulator.updateCC3DModule(flexDiffXMLData)    
                    
                    
    

#############################################################################################################################################################                               
class inSilicoLineageTracingSteppable(SteppableBasePy):    

    def __init__(self,_simulator,_frequency=1):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        
#     def start(self):
#         for cell in self.cellListByType(self.PRET):
#             cell.dict["insilicoTracing"] = [0,0,0] 
        
    def step(self,mcs):
        a = 0
        
#         # lineage trace inside -> out if there are adipocytes
#         if mcs == 360 and a<20:                               
#             for cell in self.cellListByType(self.QRET):
#                 cellNeighborList=self.getCellNeighbors(cell)
#                 for neigh in cellNeighborList:           
#                     if (neigh.neighborAddress and neigh.neighborAddress.type == self.ADIPOCYTES):
#                         cell.type=self.QPAP
#                         a+=1
        
#         lineage trace middle
        if mcs == 300: 
            a = 0                              
            for cell in self.cellListByType(self.PPAP):
                    cellNeighborList=self.getCellNeighbors(cell)
                    for neigh in cellNeighborList:           
                        if (neigh.neighborAddress and neigh.neighborAddress.type == self.QRET):
                            cell.type=self.PRET
                            
        
#         # lineage trace inside -> out
#         if mcs == 300: 
#             a = 0                              
#             for cell in self.cellListByType(self.QRET):
#                 if a <= 500:
#                     cellNeighborList=self.getCellNeighbors(cell)
#                     for neigh in cellNeighborList:           
#                         if (neigh.neighborAddress and neigh.neighborAddress.type == self.LUMEN):
#                             cell.type=self.QPAP
#                             a+=1
#                             break
#                 else:
#                     break
        
        
#         # lineage trace outside -> in
        
#         if mcs == 300:                               
#             for cell in self.cellListByType(self.PPAP):
#                 cellNeighborList=self.getCellNeighbors(cell)
#                 for neigh in cellNeighborList:           
#                     if (neigh.neighborAddress and neigh.neighborAddress.type == self.EPIDERMIS):# and a<500):
#                         cell.type=self.PRET
# #                         a = a+1    
#                         break            
                
            # track epidermal cells at labelling time
            fileName='epidermis_start.csv'
            try:
                fileHandle,fullFileName\
                =self.openFileInSimulationOutputDirectory(fileName,"w")
            except IOError:
                print("Could not open file ", fileName," for writing. ")
                return
                
            for cell in self.cellListByType(self.EPIDERMIS):
                cellNeighborList=self.getCellNeighbors(cell)
                for neigh in cellNeighborList:           
                    if neigh.neighborAddress:
                        pass
                    else:
                        print >>fileHandle, mcs,cell.id,cell.type,cell.xCOM,cell.yCOM,cell.zCOM
                        break
            fileHandle.close()
            
            # lumen border at labelling time
            fileName='adipocytes_start.csv'
            try:
                fileHandle,fullFileName\
                =self.openFileInSimulationOutputDirectory(fileName,"w")
            except IOError:
                print ("Could not open file ", fileName," for writing. ")
                return
                
            for cell in self.cellList:
                cellNeighborList=self.getCellNeighbors(cell)
                for neigh in cellNeighborList:           
                    if (neigh.neighborAddress and neigh.neighborAddress.type == self.LUMEN):
                        print >>fileHandle, mcs,cell.id,cell.type,cell.xCOM,cell.yCOM,cell.zCOM
                        break
            fileHandle.close()
        
        
        if mcs >=200:
            # track cells after labelling
            # epidermis - keep re-writting
            fileName='epidermis_end.csv'
            try:
                fileHandle,fullFileName\
                =self.openFileInSimulationOutputDirectory(fileName,"w")
            except IOError:
                print ("Could not open file ", fileName," for writing. ")
                return
                
            for cell in self.cellListByType(self.EPIDERMIS):
                for neighbor , commonSurfaceArea in self.getCellNeighborDataList(cell):                
                    if neighbor:
                        pass
                    else:
                        print >>fileHandle, mcs,cell.id,cell.type,cell.xCOM,cell.yCOM,cell.zCOM
                        break
            
    #             print >>fileHandle, 'cell.id=',cell.id,'cell.type=',cell.type,'xcom=',cell.xCOM,'ycom=',cell.yCOM,'zcom=',cell.xCOM
    
            fileHandle.close()
            
            # lumen border - keep re-writting
            fileName='adipocytes_end.csv'
            try:
                fileHandle,fullFileName\
                =self.openFileInSimulationOutputDirectory(fileName,"w")
            except IOError:
                print ("Could not open file ", fileName," for writing. ")
                return
                
            for cell in self.cellList:
                cellNeighborList=self.getCellNeighbors(cell)
                for neigh in cellNeighborList:           
                    if (neigh.neighborAddress and neigh.neighborAddress.type == self.LUMEN):
                        print >>fileHandle, mcs,cell.id,cell.type,cell.xCOM,cell.yCOM,cell.zCOM
                        break
            fileHandle.close()
            
            fileName='myOutput+'+str(mcs)+'.csv'
            try:
                fileHandle,fullFileName\
                =self.openFileInSimulationOutputDirectory(fileName,"w")
            except IOError:
                print ("Could not open file ", fileName," for writing. ")
                return
            labelledCells = []
            for cell in self.cellListByType(self.PRET,self.QPAP,self.FATTY):
                print >>fileHandle, mcs,cell.id,cell.type,cell.xCOM,cell.yCOM,cell.zCOM
            
    #             print >>fileHandle, 'cell.id=',cell.id,'cell.type=',cell.type,'xcom=',cell.xCOM,'ycom=',cell.yCOM,'zcom=',cell.xCOM
            fileHandle.close()



class SteadyStateDiffusionSteeringSteppable(SteppableBasePy):
    def __init__(self,_simulator,_frequency):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        self.simulator=_simulator


#class SecretionSteeringSteppable(SteppablePy):  ###jps make compatable with CC3D 3.7.8
class SecretionSteeringSteppable(SteppableBasePy):
    def __init__(self,_simulator,_frequency=100):
#        SteppablePy.__init__(self,_frequency)  ###jps make compatable with CC3D 3.7.8
         SteppableBasePy.__init__(self,_simulator,_frequency)
#        self.simulator=_simulator  ###jps make compatable with CC3D 3.7.8
    def step(self,mcs):
        
        if mcs > 1205:
            # get <Plugin Name="Chemotaxis"> section of XML file
            secretionXMLData=self.simulator.getCC3DModuleData("Plugin","Secretion")
            # check if we were able to successfully get the section from simulator
            if secretionXMLData:
                # get <ChemicalField Source="FlexibleDiffusionSolverFE" Name="ATTR" >
                secretionField=secretionXMLData.getFirstElement("Field",\
                d2mss({"Name":"WoundHealingSignal"}))
                # check if the attempt was succesful
                if secretionField:
                    # get <ChemotaxisByType Type="Macrophage" Lambda="xxx"/>
                    secretionWHElement=secretionField.\
                    getFirstElement("Secretion",d2mss({"Type":"IC"}))
                    if secretionWHElement:
                        # get value of Lambda from <ChemotaxisByType> element
                        # notice that no conversion fro strin to float is necessary as
                        #getAttributeAsDouble returns floating point value
                        secretionConst=float(secretionWHElement.getText())
                        # decrease lambda by 0.2
                        if secretionConst >= .1:
#                             print "lambdaVal=",secretionConst
                            secretionConst-=.01
                        else:
                            secretionConst=0
                                
                    # update attribute value of Lambda converting float to string
                    
                        secretionWHElement.updateElementValue(str(secretionConst))
            self.simulator.updateCC3DModule(secretionXMLData)









        
        

class PressureAllCells(SteppableBasePy):
    def __init__(self,_simulator,_frequency=1):
        SteppableBasePy.__init__(self,_simulator,_frequency)
        
        self.scalarCLFieldFibroblasts=CompuCellSetup.createScalarFieldCellLevelPy("pressure_cells")
        
        self.scalarCLFieldECM=CompuCellSetup.createScalarFieldCellLevelPy("pressure_ECM")
        
    def step(self,mcs):
        self.scalarCLFieldFibroblasts.clear()
        self.scalarCLFieldECM.clear()
        
        for cell in self.cellListByType(self.PPAP,self.QRET):
            self.scalarCLFieldFibroblasts[cell]= cell.targetVolume - cell.volume
        
        for cell in self.cellListByType(self.ECM):
            self.scalarCLFieldECM[cell]= cell.targetVolume - cell.volume
            
    




class codenotinuse(SteppableBasePy):    

    def __init__(self,_simulator,_frequency=1):
        SteppableBasePy.__init__(self,_simulator,_frequency)
#############################################################################################################################################################                               
################################################################# code_currently_not_in_use #################################################################
#############################################################################################################################################################                 
#  code_currently_not_in_use:

# class DynamicTissueGrowth(SteppableBasePy):    

#     def __init__(self,_simulator,_frequency=1):
#         SteppableBasePy.__init__(self,_simulator,_frequency)
        
#     def step(self,mcs):        
#         if mcs==10:      
#             self.resizeAndShiftLattice(_newSize=(260,260,10), _shiftVec=(10,10,1))       
#         elif mcs==1000:      
#             self.resizeAndShiftLattice(_newSize=(500,500,10), _shiftVec=(10,10,0))     
#         elif mcs==250:      
#             self.resizeAndShiftLattice(_newSize=(300,300,220), _shiftVec=(10,10,10))        



# class BuildWall3DSteppable(SteppableBasePy):    

#     def __init__(self,_simulator,_frequency=1):
#         SteppableBasePy.__init__(self,_simulator,_frequency)
#     def start(self):
        
#         self.buildWall(self.EPIDERMIS)

#     def step(self,mcs):        
#         print 'MCS=',mcs  
#         if mcs==2:      
#             self.destroyWall()
        
#         if mcs==40:
#             self.destroyWall()
#             self.resizeAndShiftLattice(_newSize=(800,800,1), _shiftVec=(0,0,0))
#             self.buildWall(self.EPIDERMIS)
#              # size of cell will be 3x3x1
#             self.cellField[10:12,10:12,0] = self.newCell(self.TYPENAME)
            
#                  x=X_POSITION
#         y=Y_POSITION
#         size=SIZE
#         cell=self.newCell(self.TYPENAME)
#         self.cellField[x:x+size-1,y:y+size-1,0]=cell # size of cell will be SIZExSIZEx1
        
        
        
        
#     def finish(self):
#         # Finish Function gets called after the last MCS
#         pass

# look at this for inspiration to change lattice size
# class GrowthSteppable(SteppableBasePy):
#     def __init__(self,_simulator,_frequency=1):
#         SteppableBasePy.__init__(self,_simulator,_frequency)
#     def step(self,mcs):
#         for cell in self.cellList:
#             cell.targetVolume+=1        
    # alternatively if you want to make growth a function of chemical concentration uncomment lines below and comment lines above        
        # field=CompuCell.getConcentrationField(self.simulator,"PUT_NAME_OF_CHEMICAL_FIELD_HERE")
        # pt=CompuCell.Point3D()
        # for cell in self.cellList:
            # pt.x=int(cell.xCOM)
            # pt.y=int(cell.yCOM)
            # pt.z=int(cell.zCOM)
            # concentrationAtCOM=field.get(pt)
            # cell.targetVolume+=0.01*concentrationAtCOM  # you can use here any fcn of concentrationAtCOM    

####################################################################################  
   
       
# class FuseECMSteppable(SteppableBasePy):
#     def __init__(self,_simulator,_frequency=50):
#         SteppableBasePy.__init__(self,_simulator,_frequency)
    
#     def Merging(self,cell,cellD):
#         L=[];
#         pixelList=CellPixelList(self.pixelTrackerPlugin,cellD);
        
#         for pixelData in pixelList:
#             L.append(CompuCell.Point3D(pixelData.pixel))
#             cell.targetVolume+=cellD.targetVolume
        
#         for pt in L:
#             self.cellField.set(pt,cell)
#             self.cleanDeadCells()

#     def step(self,mcs):
#         for cell in self.cellList:
#             if cell.type==self.ECM:
#                 for neighbor in self.getCellNeighborDataList(cell):
#                     if neighbor and neighbor.type == self.ECM:
#                         self.Merging(cell,neighbor)
#             break
#                         print "neighbor.id",neighbor.id," commonSurfaceArea=",commonSurfaceArea
#             else:
#                 print "Medium commonSurfaceArea=", commonSurfaceArea
#                     field=CompuCell.getConcentrationField(self.simulator,"EpidermalGrowthSignal")
#                     pt=CompuCell.Point3D()
#                     pt.x=int(cell.xCOM)
#                     pt.y=int(cell.yCOM)
#                     pt.z=int(cell.zCOM)
#                     concentrationAtCOM=field.get(pt)
#                     if concentrationAtCOM<500:  # you can use here any fcn of concentrationAtCOM     
#                         cell.type=self.QRET

####################################################################################  
        




