from PySteppables import *
import CompuCell
import sys
import os
from random import randint, shuffle, random
from math import sqrt
from PySteppablesExamples import MitosisSteppableBase
from PlayerPython import *
from math import *
import numpy as np
##class for initialization
class initializer(SteppableBasePy):
	def __init__(self, simulator, frequency, wall_w, Nx, Ny, lambda_v, Necto, ecto_wd, ecto_ht, pB,
				 pA, pL, leng_dm1, bre_dm1):
		SteppableBasePy.__init__(self, simulator, frequency)
		self.wall_w = wall_w
		self.Nx = Nx
		self.Ny = Ny
		self.lambda_v = lambda_v
		self.Necto = Necto
		self.ecto_wd = ecto_wd
		self.ecto_ht = ecto_ht
		self.pB = pB
		self.pA = pA
		self.pL = pL
		self.leng_dm1 = leng_dm1
		self.bre_dm1 = bre_dm1
		self.tV = self.leng_dm1 * self.bre_dm1
	def start(self):
		#initializing fixed wall at the rostral and caudal ends
		wall_a = self.newCell(self.WALL)
		self.cellField[0:self.wall_w - 1, 0:self.dim.y - 1, 0] = wall_a
		wall_b = self.newCell(self.WALL)
		self.cellField[self.dim.x - self.wall_w:self.dim.x - 1, 0:self.dim.y - 1, 0] = wall_b
		for cell in self.cellListByType(self.WALL):
			cell.targetVolume = cell.volume
			cell.lambdaVolume = 1000
		#initializing ecm cell layers at the top
		valy = self.dim.y
		for xc in range(1, self.Necto + 1):
			valx = self.wall_w + (xc - 1) * (self.ecto_wd)
			celle = self.newCell(self.ECM)
			self.cellField[valx:valx + self.ecto_wd - 1, valy - self.ecto_ht:valy - 1, 0] = celle
			celle.targetVolume = self.ecto_wd * self.ecto_ht
			celle.lambdaVolume = 500  
		#########################################
		#initialization of the epithelial cells below
		valcell = valy - self.ecto_ht
		total_pixels = self.leng_dm1 * self.bre_dm1
		lat_per = int(self.pL * total_pixels + 0.5)
		basal_per = int(self.pB * total_pixels + 0.5)
		apical_per = int(self.pA * total_pixels + 0.5)
		for xc in range(1, self.Nx + 1):
			valx = self.wall_w + (xc - 1) * (self.bre_dm1)
			for yc in range(1, self.Ny + 1):
				valy = valcell - (yc - 1) * (self.leng_dm1)  
				cell = self.newCell(self.LATERAL_A)	# create Lateral cell
				cella = self.newCell(self.APICAL_A) # create Apical cell
				reassignIdFlag = self.inventory.reassignClusterId(cella, cell.clusterId)
				cellb = self.newCell(self.BASAL_A)  # create Basal cell
				reassignIdFlag = self.inventory.reassignClusterId(cellb, cell.clusterId)
				xmin = valx
				xmax = valx + self.bre_dm1
				ymin = valy - self.leng_dm1
				ymax = valy
				count = 0
				for y in range(ymin, ymax):
					for x in range(xmin, xmax):
						count += 1
						if (count <= apical_per):
							self.cellField[x, y, 0] = cella
						elif (count <= (apical_per + lat_per)):
							self.cellField[x, y, 0] = cell
						elif (count <= (basal_per + lat_per + apical_per)):
							self.cellField[x, y, 0] = cellb
				cell.targetVolume = int(self.pL * total_pixels + 0.5)
				cell.lambdaVolume = self.lambda_v
				#APICAL subcell
				cella.targetVolume = int(self.pA * total_pixels + 0.5)
				cella.lambdaVolume = self.lambda_v
				#BASAL subcell
				cellb.targetVolume = int(self.pB * total_pixels + 0.5)
				cellb.lambdaVolume = self.lambda_v
				#additionally fixing the final caudal cell to avoid boundary effects
				if (xc == 1):
					cell.lambdaVolume = 1500  
					cella.lambdaVolume = 1500  
					cellb.lambdaVolume = 1500
				#dictionaries attributes attached to the cells
				cell.dict['constrict'] = 0 # attribute to check if cell is activated by wave
				cella.dict['constrict'] = 0
				cellb.dict['constrict'] = 0
				cella.dict['pairlinks'] = [] # attribute to keep track of neighbor connections
				cella.dict['fpp_to_del'] = [] # attribute to keep track of broken link neighbors
######################################################################################
#class to set up internal and initial external links
class linkadder(SteppableBasePy):
	def __init__(self, simulator, frequency, LamFP_c, LamFP_j, max_lambda):
		SteppableBasePy.__init__(self, simulator, frequency)
		self.LamFP_c = LamFP_c
		self.LamFP_j = LamFP_j
		self.min_length = 3
	def start(self):
		for cell in self.cellListByType(self.LATERAL_A):
			#function implements internal links according to Eq.3 
			self.elongation_initiate(cell)
			#function implements external links according to Eq.5
			self.junction(cell)
	def complist(self, cell):
		l = []
		complist = self.inventory.getClusterCells(cell.clusterId)
		for cellb in complist:
			if (cellb.type == self.BASAL_A):
				bas = cellb
			elif (cellb.type == self.APICAL_A):
				ap = cellb
			elif (cellb.type == self.LATERAL_A):
				lat = cellb
		l = [bas, ap, lat]
		return l
	def elongation_initiate(self, cell):
		bas = self.complist(cell)[0]
		ap = self.complist(cell)[1]
		#lateral and apical internal links 		
		dist1 = sqrt((ap.xCOM - cell.xCOM) ** 2 + (ap.yCOM - cell.yCOM) ** 2)		
		self.focalPointPlasticityPlugin.deleteInternalFocalPointPlasticityLink(cell, ap)
		self.focalPointPlasticityPlugin.createInternalFocalPointPlasticityLink(cell, ap, self.LamFP_c, dist1,
																			   self.dim.y)
		
		#lateral and basal internal links		
		dist2 = sqrt((bas.xCOM - cell.xCOM) ** 2 + (bas.yCOM - cell.yCOM) ** 2)
		self.focalPointPlasticityPlugin.deleteInternalFocalPointPlasticityLink(cell, bas)
		self.focalPointPlasticityPlugin.createInternalFocalPointPlasticityLink(cell, bas, self.LamFP_c,
																			   dist2,
																			   self.dim.y)
		#apical and basal internal links				
		dist3 = sqrt((bas.xCOM - ap.xCOM) ** 2 + (bas.yCOM - ap.yCOM) ** 2)
		self.focalPointPlasticityPlugin.deleteInternalFocalPointPlasticityLink(ap, bas)
		self.focalPointPlasticityPlugin.createInternalFocalPointPlasticityLink(ap, bas, self.LamFP_c, dist3,
																			   self.dim.y)
			
	def junction(self, cell):
		bas = self.complist(cell)[0]
		ap = self.complist(cell)[1]
		for neighbor, cS in self.getCellNeighborDataList(cell):
			if (neighbor and (neighbor.type == self.LATERAL_A)):
				complist_b = self.inventory.getClusterCells(neighbor.clusterId)
				for cell3 in complist_b:
					if (cell3.type == self.BASAL_A):
						bas_2 = cell3
					elif (cell3.type == self.APICAL_A):
						ap_2 = cell3
				#neighboring apical neighbor links
				self.focalPointPlasticityPlugin.deleteFocalPointPlasticityLink(ap, ap_2)
				dist_a = sqrt((ap.xCOM - ap_2.xCOM) ** 2 + (ap.yCOM - ap_2.yCOM) ** 2)
				self.focalPointPlasticityPlugin.createFocalPointPlasticityLink(ap, ap_2, self.LamFP_j, self.min_length,
																			   30.0)
				#neighboring basal neighbor links				
				self.focalPointPlasticityPlugin.deleteFocalPointPlasticityLink(bas, bas_2)
				dist_b = sqrt((bas.xCOM - bas_2.xCOM) ** 2 + (bas.yCOM - bas_2.yCOM) ** 2)
				self.focalPointPlasticityPlugin.createFocalPointPlasticityLink(bas, bas_2, 100, dist_b, 30.0)
				ap.dict['pairlinks'].append(ap_2.id)
				ap_2.dict['pairlinks'].append(ap.id)
################################################################################################
################class generates the caudally progressing wave###################################
################Speed of progression is wave speed (W)
################################################################################################
class signal_constrict(SteppableBasePy):
	def __init__(self, simulator, frequency, relax_time, wave_speed):
		SteppableBasePy.__init__(self, simulator, frequency)
		self.relax_time = relax_time 
		self.N = 1
		self.wave_speed = wave_speed
	def start(self):
		#self.cellListByType's order is from left to right, reversing order to implement wave right(rostral) to left(caudal)
		self.cell_list = []
		for cell in self.cellListByType(self.LATERAL_A):  
			self.cell_list.append((cell.id, cell.xCOM))
		self.cell_list = sorted(self.cell_list, key=lambda x: x[1], reverse=True)
		self.cell_list = [self.cell_list[ind][0] for ind in range(len(self.cell_list))]
		###############################################################################
		counter = 1
		for id in self.cell_list:
			cell = self.attemptFetchingCellById(id)
			ap = self.complist(cell)[1]
			cell.dict['position'] = counter# gives the cells a position number 
			ap.dict['position'] = counter
			counter = counter + 1
		################################################################################
		self.start = 0  # instead of 0
		self.fin = self.N
	#####################################
	#####################################
	##########################################
	##########################################
	def step(self, mcs):
		#The wave is applied after the simulation has relaxed for a few mcs after
		#creating the initial conditions
		time = mcs - self.relax_time 
		if (time % self.wave_speed == 0):
			self.diff_list = []
			sl = self.cell_list[self.start:self.fin]
			for cellid in sl:
				cell = self.attemptFetchingCellById(cellid)
				bas = self.complist(cell)[0]
				ap = self.complist(cell)[1]
				cell.dict['constrict'] = 1
				bas.dict['constrict'] = 1
				ap.dict['constrict'] = 1
			self.start = self.fin
			self.fin = min(self.fin + self.N, len(self.cell_list))
	def complist(self, cell):
		l = []
		complist = self.inventory.getClusterCells(cell.clusterId)
		for cellb in complist:
			if (cellb.type == self.BASAL_A):
				bas = cellb
			elif (cellb.type == self.APICAL_A):
				ap = cellb
			elif (cellb.type == self.LATERAL_A):
				lat = cellb
		l = [bas, ap, lat]
		return l
##############################################################################
#############class initiates pair wise contriction for cell neighbors
#############passed by the constriction wave##################################
#############parameters are (1) rate, which is the rate of apical contractility 
#############(2) LamFP_j, which is the strength of the junctional links (lambda_a) as in Eq. 5
#############(3) wave speed is the speed of caudal activation of cells
#############(4) max_lambda is the maximum value of lambda_a as in Eq. 5
#############(5) cutoff is the value of the breaking tension
##############################################################################
class constrict(SteppableBasePy):
	def __init__(self, simulator, frequency, bre_dm1, leng_dm1, LamFP_j, rate, Nset, relax_time, wave_speed, max_lambda,
				 cutoff):
		SteppableBasePy.__init__(self, simulator, frequency)
		self.constric_rate_ap = rate
		self.LamFP_j = LamFP_j
		self.Nset = Nset
		self.wave_speed = wave_speed
		self.max_lambda = max_lambda
		self.cutoff = cutoff
		self.relax_time = relax_time
		self.min_length = 3
	def start(self):
		self.somite_list=[]
		pass
	def step(self, mcs):
		if (mcs >= self.relax_time):
			self.tension_calc_intersection(mcs)
			self.somite_len()
	def tension_calc_intersection(self, mcs):
		for ap in self.cellListByType(self.APICAL_A):
			ap.dict['tension_intersect'] = []# these attributes ensure the link properties are changed only once per cell
			ap.dict['tension_id'] = []
		
		#this part of the code applies pairwise contractility 
		for ap in self.cellListByType(self.APICAL_A):
			if (ap.dict['constrict'] == 1):
				for id in ap.dict['pairlinks']:
					ap_2 = self.attemptFetchingCellById(id)
					if (id not in ap.dict['tension_id'] and ap_2.dict['constrict'] == 1):
						fpp_r = self.fpp_return(ap, ap_2)
						leng = fpp_r.targetDistance
						lamb = fpp_r.lambdaDistance
						lamb = min(lamb + self.constric_rate_ap, self.max_lambda)
						self.focalPointPlasticityPlugin.setFocalPointPlasticityParameters(ap, ap_2, lamb,
																						  self.min_length, 30.0)
						ap.dict['tension_id'].append(fpp_r.neighborAddress.id)
						fpp_r.neighborAddress.dict['tension_id'].append(ap.id)

		#this part of the code applies breaking tension
		for ap in self.cellListByType(self.APICAL_A):
			for id in ap.dict['pairlinks']:
				ap_2 = self.attemptFetchingCellById(id)
				if (id not in ap.dict['tension_intersect']):
					fpp_r = self.fpp_return(ap, ap_2)
					leng = fpp_r.targetDistance
					lam_fpp = fpp_r.lambdaDistance
					dist_s = sqrt((ap.xCOM - fpp_r.neighborAddress.xCOM) ** 2 + \
								  (ap.yCOM - fpp_r.neighborAddress.yCOM) ** 2)
					ten = -2 * lam_fpp * (dist_s - leng)
					ap.dict['tension_intersect'].append(fpp_r.neighborAddress.id)
					fpp_r.neighborAddress.dict['tension_intersect'].append(ap.id)
					if (abs(ten) > self.cutoff):
						if (ap_2.id not in ap.dict['fpp_to_del']):
							ap.dict['fpp_to_del'].append(ap_2.id)
						if (ap.id not in ap_2.dict['fpp_to_del']):
							ap_2.dict['fpp_to_del'].append(ap.id)
						min_id = min(ap.dict['position'], ap_2.dict['position'])
						max_pos = self.findwherewave()
						self.somite_list.append(min_id)
		for ap in self.cellListByType(self.APICAL_A):
			for id in ap.dict['fpp_to_del']:
				ap_2 = self.attemptFetchingCellById(id)
				if (ap_2.id in ap.dict['pairlinks']):
					ap.dict['pairlinks'].remove(ap_2.id)
					ap_2.dict['pairlinks'].remove(ap.id)
					self.focalPointPlasticityPlugin.deleteFocalPointPlasticityLink(ap, ap_2)
	####################################################################################
	####this function implements the exit condition for some simulations: if the wave 
	####gets too close to the caudal edge, the simulation exits to prevent any
	####boundary effects. For very small rate of contractility, and sufficient segments
	####don't form in the course of the wave, this condition is omitted to allow the 
	####simulation to keep running after activation of all the cells. Boundary effects
	####elimininated by fixing few rostral cells 
	####################################################################################
	def somite_len(self):
		self.somite_list.sort()
		new_list = []
		for index in range(1, len(self.somite_list)):
			new_list.append(self.somite_list[index] - self.somite_list[index - 1])
		if (len(new_list) > 0):
			mean_l = sum(new_list) / float(len(new_list))
		else:
			mean_l = 0
		if (len(self.somite_list) > 0):
			if ((self.Nset - self.somite_list[-1]) < 3 * mean_l):
				sys.exit()
	#####################################################################################
	#####this function tracks the position of the wave###################################
	def findwherewave(self):
		min_wave_pos = []
		for ap in self.cellListByType(self.APICAL_A):
			if (ap.dict['constrict'] == 1):
				min_wave_pos.append(ap.dict['position'])
		max_pos = max(min_wave_pos)
		return max_pos
	def fpp_return(self, cell1, cell2):
		for fpp in self.getFocalPointPlasticityDataList(cell1):
			if (fpp.neighborAddress.id == cell2.id):
				return fpp
	def complist(self, cell):
		l = []
		complist = self.inventory.getClusterCells(cell.clusterId)
		for cellb in complist:
			if (cellb.type == self.BASAL_A):
				bas = cellb
			elif (cellb.type == self.APICAL_A):
				ap = cellb
			elif (cellb.type == self.LATERAL_A):
				lat = cellb
		l = [bas, ap, lat]
		return l

