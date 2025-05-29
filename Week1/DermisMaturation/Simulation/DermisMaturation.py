# DermisMaturation.py
# PARAMETERS:
cd=10          # Typical cell diameter
Lx=500       # Size of lattice - x
Ly=500       # Size of lattice - y
Lz=10       # Size of lattice - z

debugFreq=100

# POTTS PARAMETERS:
Temp=50              # Potts temperature
Time=2501         # Total number of MCS
NOrder=3             # NeighborOrder, flips

# CONTACT PARAMETERS:
CNOrder=4             # Distance of interaction, cell boundary

# VOLUME PARAMETERS
LamV=50                # Lambda Volume
targV=100        # Target Volume

# CONTACT INHIBITION:
gFactor=0.8          #Growth factor
hillCoef=20          #Hill coeficient
critAlpha=0.35        #Critical alpha

# LUMEN GROWTH:
Kl=1
ApArea=6.*cd*cd*.2  # ApArea=1/Kr


def configureSimulation(sim,Lx,Ly,Lz,Temp,Time,NOrder,CNOrder,debugFreq):

    import CompuCellSetup
    from XMLUtils import ElementCC3D

    CompuCell3DElement=ElementCC3D("CompuCell3D",{"Version":"3.7.5"})

    # Basic properties of CPM (GGH) algorithm
    potts=CompuCell3DElement.ElementCC3D("Potts")
    potts.ElementCC3D("Dimensions",{"x":500,"y":500,"z":10})
    potts.ElementCC3D("Temperature",{},50)
    potts.ElementCC3D("Steps",{},Time)
    potts.ElementCC3D("NeighborOrder",{},1)
    potts.ElementCC3D("DebugOutputFrequency",{},debugFreq)

    # Setting periodic boundary conditions to all directions
    potts.ElementCC3D("Boundary_x",{},"Periodic")
    potts.ElementCC3D("Boundary_y",{},"Periodic")
    potts.ElementCC3D("Boundary_z",{},"Periodic")


    # Cell Types -> Epidermis, Progenitors, PPap, QPap, PRet, QRet, Adipocytes, ECM, Lumen
    cellType=CompuCell3DElement.ElementCC3D("Plugin",{"Name":"CellType"})
    cellType.ElementCC3D("CellType",{"TypeName":"Medium","TypeId":0})
    cellType.ElementCC3D("CellType",{"TypeName":"Epidermis","TypeId":1})
    cellType.ElementCC3D("CellType",{"TypeName":"Progenitors","TypeId":2})
    cellType.ElementCC3D("CellType",{"TypeName":"PPap","TypeId":3})
    cellType.ElementCC3D("CellType",{"TypeName":"QPap","TypeId":4})
    cellType.ElementCC3D("CellType",{"TypeName":"PRet","TypeId":5})
    cellType.ElementCC3D("CellType",{"TypeName":"QRet","TypeId":6})
    cellType.ElementCC3D("CellType",{"TypeName":"Adipocytes","TypeId":7})
    cellType.ElementCC3D("CellType",{"TypeName":"ECM","TypeId":8})
    cellType.ElementCC3D("CellType",{"TypeName":"Lumen","TypeId":9})
    cellType.ElementCC3D("CellType",{"TypeName":"MyoF","TypeId":10})
    cellType.ElementCC3D("CellType",{"TypeName":"QMyoF","TypeId":11})
    cellType.ElementCC3D("CellType",{"TypeName":"BC","TypeId":12})
    cellType.ElementCC3D("CellType",{"TypeName":"IC","TypeId":13})
    cellType.ElementCC3D("CellType",{"TypeName":"Fatty","TypeId":14})


    # CELL COLORS --> not working
    cellColor=CompuCell3DElement.ElementCC3D("Plugin",{"Name":"PlayerSettings"})
    cellColor.ElementCC3D("Cell",{"Type":0,"Color":"#000000"}) # Black        -> Medium
    cellColor.ElementCC3D("Cell",{"Type":1,"Color":"#008000"}) # Green        -> Epidermis
    cellColor.ElementCC3D("Cell",{"Type":2,"Color":"#0000FF"}) # Blue         -> Progenitors
    cellColor.ElementCC3D("Cell",{"Type":3,"Color":"#FF0000"}) # Red          -> PPap
    cellColor.ElementCC3D("Cell",{"Type":4,"Color":"#990000"}) # Dark red     -> QPap
    cellColor.ElementCC3D("Cell",{"Type":5,"Color":"#FFFF00"}) # Yellow       -> PRet
    cellColor.ElementCC3D("Cell",{"Type":6,"Color":"#CCCC00"}) # Dark Yellow  -> QRet
    cellColor.ElementCC3D("Cell",{"Type":7,"Color":"#00E6E6"}) # Light blue   -> Adipocytes
    cellColor.ElementCC3D("Cell",{"Type":8,"Color":"#8B1A89"}) # Purple       -> ECM
    cellColor.ElementCC3D("Cell",{"Type":9,"Color":"#D3D3D3"}) # Light grey   -> Lumen
    cellColor.ElementCC3D("Cell",{"Type":10,"Color":"#D3D3D3"}) # Light grey  -> MyoF
    cellColor.ElementCC3D("Cell",{"Type":11,"Color":"#FF0000"}) # Red         -> BC
    cellColor.ElementCC3D("Cell",{"Type":12,"Color":"#FF0000"}) # Red         -> IC
    cellColor.ElementCC3D("Cell",{"Type":13,"Color":"#00E6E6"}) # Light blue   -> Fatty
#     cellColor.ElementCC3D("TypesInvisibleIn3D",{"Types":"0,9"})   # Don't show Medium and Lumen
    cellColor.ElementCC3D("VisualControl",{"ScreenshotFrequency":250,"ScreenUpdateFrequency":10})


#     # Cell Colors
#     cellColor=CompuCell3DElement.ElementCC3D("Plugin",{"Name":"PlayerSettings"})
#     cellColor.ElementCC3D("Cell",{"Type":0,"Color":"#000000"}) # Black        -> Medium
#     cellColor.ElementCC3D("Cell",{"Type":1,"Color":"black"}) # Green        -> Epidermis
#     cellColor.ElementCC3D("Cell",{"Type":2,"Color":"blue"}) # Blue         -> Progenitors
#     cellColor.ElementCC3D("Cell",{"Type":3,"Color":"green"}) # Red          -> PPap
#     cellColor.ElementCC3D("Cell",{"Type":4,"Color":"#990000"}) # Dark red     -> QPap
#     cellColor.ElementCC3D("Cell",{"Type":5,"Color":"cyan"}) # Yellow       -> PRet
#     cellColor.ElementCC3D("Cell",{"Type":6,"Color":"#CCCC00"}) # Dark Yellow  -> QRet
#     cellColor.ElementCC3D("Cell",{"Type":7,"Color":"#00E6E6"}) # Light blue   -> Adipocytes
#     cellColor.ElementCC3D("Cell",{"Type":8,"Color":"#8B1A89"}) # Purple       -> ECM
#     cellColor.ElementCC3D("Cell",{"Type":9,"Color":"#D3D3D3"}) # Light grey   -> Lumen
#     cellColor.ElementCC3D("Cell",{"Type":10,"Color":"#D3D3D3"}) # Light grey  -> MyoF
#     cellColor.ElementCC3D("Cell",{"Type":11,"Color":"red"}) # Red         -> BC
#     cellColor.ElementCC3D("Cell",{"Type":12,"Color":"red"}) # Red         -> BCtop
# #     cellColor.ElementCC3D("TypesInvisibleIn3D",{"Types":"0,9"})   # Don't show Medium and Lumen
#     cellColor.ElementCC3D("VisualControl",{"ScreenshotFrequency":250,"ScreenUpdateFrequency":10})


    # Specification of adhesion energies
    contact=CompuCell3DElement.ElementCC3D("Plugin",{"Name":"Contact"})
    
#     #MEDIUM
#     contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Medium"},0)
#     contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Epidermis"},2)
#     contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Progenitors"},100)
#     contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"PPap"},100)
#     contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"QPap"},100)
#     contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"PRet"},100)
#     contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"QRet"},100)
#     contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Adipocytes"},100)
#     contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"ECM"},100)
#     contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Lumen"},100)

#     #ECM
#     contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"ECM"},1)
#     contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"Epidermis"},50)
#     contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"Progenitors"},20)
#     contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"PPap"},2)
#     contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"QPap"},20)
#     contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"PRet"},2)
#     contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"QRet"},1)
#     contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"Adipocytes"},50)
#     contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"Lumen"},20)

#     #EPIDERMIS
#     contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"Epidermis"},2)
#     contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"Progenitors"},5)
#     contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"PPap"},10)
#     contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"QPap"},10)
#     contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"PRet"},20)
#     contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"QRet"},20)
#     contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"Adipocytes"},100)
#     contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"Lumen"},100)

#     #PROGENITORS
#     contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"Progenitors"},10)
#     contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"PPap"},10)
#     contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"QPap"},10)
#     contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"PRet"},10)
#     contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"QRet"},10)
#     contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"Adipocytes"},10)
#     contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"Lumen"},100)

#     #PPAP
#     contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"PPap"},20)
#     contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"QPap"},10)
#     contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"PRet"},10)
#     contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"QRet"},20)
#     contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"Adipocytes"},100)
#     contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"Lumen"},100)

#     #QPAP
#     contact.ElementCC3D("Energy",{"Type1":"QPap","Type2":"QPap"},10)
#     contact.ElementCC3D("Energy",{"Type1":"QPap","Type2":"PRet"},20)
#     contact.ElementCC3D("Energy",{"Type1":"QPap","Type2":"QRet"},10)
#     contact.ElementCC3D("Energy",{"Type1":"QPap","Type2":"Adipocytes"},100)
#     contact.ElementCC3D("Energy",{"Type1":"QPap","Type2":"Lumen"},100)

#     #PRET
#     contact.ElementCC3D("Energy",{"Type1":"PRet","Type2":"PRet"},10)
#     contact.ElementCC3D("Energy",{"Type1":"PRet","Type2":"QRet"},10)
#     contact.ElementCC3D("Energy",{"Type1":"PRet","Type2":"Adipocytes"},100)
#     contact.ElementCC3D("Energy",{"Type1":"PRet","Type2":"Lumen"},100)

#     #QRET
#     # 24/01/2017: considere increase QRet QRet
#     contact.ElementCC3D("Energy",{"Type1":"QRet","Type2":"QRet"},20)
#     contact.ElementCC3D("Energy",{"Type1":"QRet","Type2":"Adipocytes"},50)
#     contact.ElementCC3D("Energy",{"Type1":"QRet","Type2":"Lumen"},100)

#     #ADIPOCYTES
#     contact.ElementCC3D("Energy",{"Type1":"Adipocytes","Type2":"Adipocytes"},2)
#     contact.ElementCC3D("Energy",{"Type1":"Adipocytes","Type2":"Lumen"},10)

#     #LUMEN
#     contact.ElementCC3D("Energy",{"Type1":"Lumen","Type2":"Lumen"},1)
    
############# bellow is the current code ##############

    #MEDIUM
    contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Medium"},0)
    contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Epidermis"},2)
    contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Progenitors"},50)
    contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"PPap"},50)
    contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"QPap"},50)
    contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"PRet"},50)
    contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"QRet"},50)
    contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Adipocytes"},50)
    contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"ECM"},50)
    contact.ElementCC3D("Energy",{"Type1":"Medium","Type2":"Lumen"},50)

    #ECM
    contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"ECM"},5)
    contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"Epidermis"},10)
    contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"Progenitors"},2)
    contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"PPap"},2) 
    contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"QPap"},2)
    contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"PRet"},2)
    contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"QRet"},2)
    contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"Adipocytes"},30) #changed from 50
    contact.ElementCC3D("Energy",{"Type1":"ECM","Type2":"Lumen"},30)

    #EPIDERMIS
    contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"Epidermis"},2)
    contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"Progenitors"},5) 
    contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"PPap"},10)
    contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"QPap"},10)
    contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"PRet"},10) #changed from 20
    contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"QRet"},10) #changed from 20
    contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"Adipocytes"},30) #changed from 100
    contact.ElementCC3D("Energy",{"Type1":"Epidermis","Type2":"Lumen"},50) #changed from100

    #PROGENITORS
    contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"Progenitors"},10)
    contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"PPap"},10)
    contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"QPap"},10)
    contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"PRet"},10)
    contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"QRet"},10)
    contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"Adipocytes"},30) # changed from 10
    contact.ElementCC3D("Energy",{"Type1":"Progenitors","Type2":"Lumen"},50)

    #PPAP
    contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"PPap"},5) # changed from 20
    contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"QPap"},5)
    contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"PRet"},5) # changed from 10
    contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"QRet"},5) # changed from 20
    contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"Adipocytes"},30) #changed from 100
    contact.ElementCC3D("Energy",{"Type1":"PPap","Type2":"Lumen"},50) #changed from 100

    #QPAP
    contact.ElementCC3D("Energy",{"Type1":"QPap","Type2":"QPap"},5) # changed from 10
    contact.ElementCC3D("Energy",{"Type1":"QPap","Type2":"PRet"},5) # changed from 20
    contact.ElementCC3D("Energy",{"Type1":"QPap","Type2":"QRet"},5) # changed from 10
    contact.ElementCC3D("Energy",{"Type1":"QPap","Type2":"Adipocytes"},30) #changed from 100
    contact.ElementCC3D("Energy",{"Type1":"QPap","Type2":"Lumen"},30) #changed from 100

    #PRET
    contact.ElementCC3D("Energy",{"Type1":"PRet","Type2":"PRet"},5) #changed from 5
    contact.ElementCC3D("Energy",{"Type1":"PRet","Type2":"QRet"},5)
    contact.ElementCC3D("Energy",{"Type1":"PRet","Type2":"Adipocytes"},30) #changed from 100
    contact.ElementCC3D("Energy",{"Type1":"PRet","Type2":"Lumen"},50) #changed from 100

    #QRET
    contact.ElementCC3D("Energy",{"Type1":"QRet","Type2":"QRet"},5) # changed from 20
    contact.ElementCC3D("Energy",{"Type1":"QRet","Type2":"Adipocytes"},30) # changed from 50
    contact.ElementCC3D("Energy",{"Type1":"QRet","Type2":"Lumen"},30) # changed from 100

    #ADIPOCYTES
    contact.ElementCC3D("Energy",{"Type1":"Adipocytes","Type2":"Adipocytes"},2)
    contact.ElementCC3D("Energy",{"Type1":"Adipocytes","Type2":"Lumen"},10)

    #LUMEN
    contact.ElementCC3D("Energy",{"Type1":"Lumen","Type2":"Lumen"},1)

    #FATTYs
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"Fatty"},2)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"IC"},10)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"BC"},100)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"Medium"},100)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"ECM"},5)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"Epidermis"},30)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"Progenitors"},10)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"PPap"},30)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"QPap"},30)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"PRet"},30)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"QRet"},30)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"Adipocytes"},2)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"Lumen"},10)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"MyoF"},20)
    contact.ElementCC3D("Energy",{"Type1":"Fatty","Type2":"QMyoF"},20)

    #MYOF
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"MyoF"},2)
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"Medium"},100)
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"ECM"},100)
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"Epidermis"},10)
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"Progenitors"},10)
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"PPap"},10)
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"QPap"},10)
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"PRet"},10)
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"QRet"},10)
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"Adipocytes"},20)
    contact.ElementCC3D("Energy",{"Type1":"MyoF","Type2":"Lumen"},100)

    #QMYOF
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"QMyoF"},5)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"Medium"},50)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"ECM"},1)#changed from 100
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"Epidermis"},10)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"Progenitors"},10)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"PPap"},10)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"QPap"},5)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"PRet"},10)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"QRet"},5)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"Adipocytes"},20)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"Lumen"},20)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"MyoF"},10)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"BC"},100)
    contact.ElementCC3D("Energy",{"Type1":"QMyoF","Type2":"IC"},10)

    #BLOOD CLOT
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"BC"},2)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"Medium"},2)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"ECM"},100)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"Epidermis"},30)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"Progenitors"},100)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"PPap"},100)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"QPap"},100)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"PRet"},100)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"QRet"},100)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"Adipocytes"},100)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"Lumen"},100)
    contact.ElementCC3D("Energy",{"Type1":"BC","Type2":"MyoF"},100)

    #IMMUNE CELLS & COMPANY
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"IC"},5)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"BC"},100)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"Medium"},100)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"ECM"},10)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"Epidermis"},30)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"Progenitors"},10)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"PPap"},10)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"QPap"},10)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"PRet"},10)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"QRet"},10)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"Adipocytes"},10)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"Lumen"},50)
    contact.ElementCC3D("Energy",{"Type1":"IC","Type2":"MyoF"},2)

    #Neighbor order
    contact.ElementCC3D("NeighborOrder",{},CNOrder)# changed to CNOrder instead of 5

    #OTHER PLUGINS

    boundaryPTracker=CompuCell3DElement.ElementCC3D("Plugin",{"Name":"BoundaryPixelTracker"})
#     boundaryPTracker.ElementCC3D("NeighborOrder",{},"1")

    vlFlex=CompuCell3DElement.ElementCC3D("Plugin",{"Name":"VolumeLocalFlex"})

    coMass=CompuCell3DElement.ElementCC3D("Plugin",{"Name":"CenterOfMass"})

    neighborTracker=CompuCell3DElement.ElementCC3D("Plugin",{"Name":"NeighborTracker"})

    SteppableElmnt=CompuCell3DElement.ElementCC3D("Steppable",{"Type":"BoxWatcher"})

    # Module tracing boundaries of the minimal box enclosing all the cells. May speed up calculations. May have no effect for parallel version
    SteppableElmnt.ElementCC3D("XMargin",{},"5")
    SteppableElmnt.ElementCC3D("YMargin",{},"5")
    SteppableElmnt.ElementCC3D("ZMargin",{},"5")


    # Secretion
    secretion=CompuCell3DElement.ElementCC3D("Plugin",{"Name":"Secretion"})
#     secretionchemicalField1=secretion.ElementCC3D("Field", {"Name":"EpidermalGrowthSignal"})
#     secretionchemicalField1.ElementCC3D("Secretion",{"Type":"Epidermis"},"10.0")
#     secretionchemicalField2=secretion.ElementCC3D("Field", {"Name":"ECMSignal"})
#     secretionchemicalField2.ElementCC3D("Secretion",{"Type":"Lumen"},"100.0")
# #     secretionchemicalField2.ElementCC3D("Secretion",{"Type":"ECM"},"5.0")
#     secretionchemicalField2.ElementCC3D("Secretion",{"Type":"QRet"},"5.0")
#     secretionchemicalField2.ElementCC3D("Secretion",{"Type":"QPap"},"5.0")
    secretionchemicalField3=secretion.ElementCC3D("Field",{"Name":"WoundHealingSignal"})
    secretionchemicalField3.ElementCC3D("Secretion",{"Type":"IC"},"1.0")
#     secretionchemicalField3.ElementCC3D("SecretionOnContact",{"SecreteOnContactWith":"Progenitors, PPap, QRet","Type":"MyoF"},"50.0")


    # Chemotaxis
    chemotaxis=CompuCell3DElement.ElementCC3D("Plugin",{"Name":"Chemotaxis"})
#     chemicalFieldEGF=chemotaxis.ElementCC3D("ChemicalField", {"Source":"DiffusionSolverFE", "Name":"EpidermalGrowthSignal"})
    chemicalFieldWH=chemotaxis.ElementCC3D("ChemicalField", {"Source":"DiffusionSolverFE", "Name":"WoundHealingSignal"})
    chemicalFieldWH.ElementCC3D("ChemotaxisByType", {"Type":"MyoF" ,"Lambda":-10})
    chemicalFieldWH.ElementCC3D("ChemotaxisByType", {"Type":"MyoF" ,"Epidermis":-100})


    # Specification of PDE solvers
    flexDiffSolver1=CompuCell3DElement.ElementCC3D("Steppable",{"Type":"SteadyStateDiffusionSolver2D"})
    diffusionFieldEGF=flexDiffSolver1.ElementCC3D("DiffusionField")
    diffusionDataEGF=diffusionFieldEGF.ElementCC3D("DiffusionData")
    diffusionDataEGF.ElementCC3D("FieldName",{},"EpidermalGrowthSignal")
#     diffusionDataEGF.ElementCC3D("GlobalDiffusionConstant",{},1e-1)
#     diffusionDataEGF.ElementCC3D("GlobalDecayConstant",{},1e-3)
    diffusionDataEGF.ElementCC3D("DiffusionConstant",{},1e-1)
    diffusionDataEGF.ElementCC3D("DecayConstant",{},1e-3)
    diffusionDataEGF.ElementCC3D("DoNotDiffuseTo",{},"Medium")
    diffusionDataEGF.ElementCC3D("DoNotDiffuseTo",{},"Lumen")
    secretionDataEGF=diffusionFieldEGF.ElementCC3D("SecretionData")
    # When secretion is defined inside DissufionSolverFEall secretio nconstants are scaled automaticly to account for extra calls of the solver when handling large diffusion constants
    # Uniform secretion Definition
    secretionDataEGF.ElementCC3D("Secretion",{"Type":"Epidermis"},"10.")
    BoundaryConditionsEGF=diffusionFieldEGF.ElementCC3D("BoundaryConditions")
    BoundaryConditionsEGF_X=BoundaryConditionsEGF.ElementCC3D("Plane",{"Axis":"X"})
    BoundaryConditionsEGF_X.ElementCC3D("ConstantValue",{"PlanePosition":"Min","Value":"0.0"})
    BoundaryConditionsEGF_X.ElementCC3D("ConstantValue",{"PlanePosition":"Max","Value":"0.0"})
    BoundaryConditionsEGF_Y=BoundaryConditionsEGF.ElementCC3D("Plane",{"Axis":"Y"})
    BoundaryConditionsEGF_Y.ElementCC3D("ConstantValue",{"PlanePosition":"Min","Value":"0.0"})
    BoundaryConditionsEGF_Y.ElementCC3D("ConstantValue",{"PlanePosition":"Max","Value":"0.0"})
    BoundaryConditionsEGF_Z=BoundaryConditionsEGF.ElementCC3D("Plane",{"Axis":"Z"})
    BoundaryConditionsEGF_Z.ElementCC3D("ConstantDerivative",{"PlanePosition":"Min","Value":"0.0"})
    BoundaryConditionsEGF_Z.ElementCC3D("ConstantDerivative",{"PlanePosition":"Max","Value":"0.0"})

    flexDiffSolver=CompuCell3DElement.ElementCC3D("Steppable",{"Type":"DiffusionSolverFE"})
#     diffusionFieldECM=flexDiffSolver.ElementCC3D("DiffusionField")
#     diffusionDataECM=diffusionFieldECM.ElementCC3D("DiffusionData")
#     diffusionDataECM.ElementCC3D("FieldName",{},"ECMSignal")
#     diffusionDataECM.ElementCC3D("DiffusionConstant",{},1e0)
#     diffusionDataECM.ElementCC3D("DecayConstant",{},1e-5)
# #     diffusionDataECM.ElementCC3D("DoNotDiffuseTo",{},"PPap")
# #     diffusionDataECM.ElementCC3D("DoNotDiffuseTo",{},"Epidermis")
#     diffusionDataECM.ElementCC3D("DoNotDiffuseTo",{},"Medium")
#     diffusionDataECM.ElementCC3D("DoNotDiffuseTo",{},"Lumen")
# #     diffusionDataECM.ElementCC3D("DecayConstant",{"CellType":"Lumen"},100)
#     secretionDataECM=diffusionFieldEGF.ElementCC3D("SecretionData")
#     # When secretion is defined inside DissufionSolverFEall secretio nconstants are scaled automaticly to account for extra calls of the solver when handling large diffusion constants
#     # Uniform secretion Definition
#     secretionDataECM.ElementCC3D("Secretion",{"Type":"Lumen"},"5.")
# #     secretionDataECM.ElementCC3D("Secretion",{"Type":"QRet"},"1.")
#     BoundaryConditionsECM=diffusionFieldECM.ElementCC3D("BoundaryConditions")
#     BoundaryConditionsECM_X=BoundaryConditionsEGF.ElementCC3D("Plane",{"Axis":"X"})
#     BoundaryConditionsECM_X.ElementCC3D("ConstantValue",{"PlanePosition":"Min","Value":"0.0"})
#     BoundaryConditionsECM_X.ElementCC3D("ConstantValue",{"PlanePosition":"Max","Value":"0.0"})
#     BoundaryConditionsECM_Y=BoundaryConditionsECM.ElementCC3D("Plane",{"Axis":"Y"})
#     BoundaryConditionsECM_Y.ElementCC3D("ConstantValue",{"PlanePosition":"Min","Value":"0.0"})
#     BoundaryConditionsECM_Y.ElementCC3D("ConstantValue",{"PlanePosition":"Max","Value":"0.0"})
#     BoundaryConditionsECM_Z=BoundaryConditionsECM.ElementCC3D("Plane",{"Axis":"Z"})
#     BoundaryConditionsECM_Z.ElementCC3D("ConstantDerivative",{"PlanePosition":"Min","Value":"0.0"})
#     BoundaryConditionsECM_Z.ElementCC3D("ConstantDerivative",{"PlanePosition":"Max","Value":"0.0"})

    diffusionFieldWH=flexDiffSolver.ElementCC3D("DiffusionField")
    diffusionDataWH=diffusionFieldWH.ElementCC3D("DiffusionData")
    diffusionDataWH.ElementCC3D("FieldName",{},"WoundHealingSignal")
    diffusionDataWH.ElementCC3D("DiffusionConstant",{},1e-0)
    diffusionDataWH.ElementCC3D("DecayConstant",{},1e-2)
#     diffusionDataWH.ElementCC3D("DoNotDiffuseTo",{},"Medium")
    diffusionDataWH.ElementCC3D("DoNotDiffuseTo",{},"Lumen")


#     pifInitializer=CompuCell3DElement.ElementCC3D("Steppable",{"Type":"PIFInitializer"})
#     pifInitializer.ElementCC3D("PIFName",{},"DermisMaturationCurrentConfiguration.piff01700.pif")

#     pifDumper=CompuCell3DElement.ElementCC3D("Steppable",{"Type":"PIFDumper","Frequency":100})
#     pifDumper.ElementCC3D("PIFName",{},"DermisMaturationCurrentConfiguration.piff")

    CompuCellSetup.setSimulationXMLDescription(CompuCell3DElement)


import CompuCellSetup
import CompuCell


import sys
from os import environ
from os import getcwd
import string

import math
from math import *

sys.path.append(environ["PYTHON_MODULE_PATH"])

pi=math.pi


sim,simthread = CompuCellSetup.getCoreSimulationObjects()
configureSimulation(sim,Lx,Ly,Lz,Temp,Time,NOrder,CNOrder,debugFreq)

CompuCellSetup.initializeSimulationObjects(sim,simthread)

# Create extra player fields here or add attibutes
pyAttributeAdder,dictAdder = CompuCellSetup.attachDictionaryToCells(sim)
# CompuCellSetup.initializeSimulationObjects(sim,simThread)

# add extra attributes here

# CompuCellSetup.initializeSimulationObjects(sim,simthread)
# Definitions of additional Python-managed fields go here

#Add Python steppables here
steppableRegistry=CompuCellSetup.getSteppableRegistry()

# set simulation
from DermisMaturationSteppables import ConstraintInitializerSteppable
ConstraintInitializerSteppableInstance=ConstraintInitializerSteppable(sim,Time,cd,targV,LamV)
steppableRegistry.registerSteppable(ConstraintInitializerSteppableInstance)


# grow cells
from DermisMaturationSteppables import GrowthSteppable
GrowthSteppableInstance=GrowthSteppable(sim,_frequency=1)
steppableRegistry.registerSteppable(GrowthSteppableInstance)


# cell division
from DermisMaturationSteppables import MitosisSteppable
MitosisSteppableInstance=MitosisSteppable(sim,_frequency=1)
steppableRegistry.registerSteppable(MitosisSteppableInstance)


# ECM production
from DermisMaturationSteppables import ECMSteppable
ECMSteppableInstance=ECMSteppable(sim,_frequency=2)
steppableRegistry.registerSteppable(ECMSteppableInstance)


# grow body inside
from DermisMaturationSteppables import LumenFlux
lFluxSteppableInstance=LumenFlux(sim,1,LamV,Kl,ApArea)
steppableRegistry.registerSteppable(lFluxSteppableInstance)


# cell fate conversion
from DermisMaturationSteppables import TransitionSteppable
TransitionSteppableInstance=TransitionSteppable(sim,_frequency=1)
steppableRegistry.registerSteppable(TransitionSteppableInstance)


# adipocytes maturation
from DermisMaturationSteppables import AdipocytesMaturationSteppable
AdipocytesMaturationSteppableInstance=AdipocytesMaturationSteppable(sim,_frequency=1)
steppableRegistry.registerSteppable(AdipocytesMaturationSteppableInstance)


# plots
from DermisMaturationSteppables import PlotCells
PlotCellsSteppableInstance=PlotCells(sim,_frequency=10)
steppableRegistry.registerSteppable(PlotCellsSteppableInstance)


# # cut the skin
# from DermisMaturationSteppables import CutRegion
# CutRegionSteppableInstance=CutRegion(sim,_frequency=1)
# steppableRegistry.registerSteppable(CutRegionSteppableInstance)


# # wound healing
# from DermisMaturationSteppables import woundHealing
# woundHealingSteppableInstance=woundHealing(sim,_frequency=1)
# steppableRegistry.registerSteppable(woundHealingSteppableInstance)


# # perform lineage tracing
# from DermisMaturationSteppables import inSilicoLineageTracingSteppable
# inSilicoLineageTracingSteppableInstance=inSilicoLineageTracingSteppable(sim,_frequency=1)
# steppableRegistry.registerSteppable(inSilicoLineageTracingSteppableInstance)


# steer parameters
# if simulating a non-decaying epidermal gradient comment the next 3 lines
from DermisMaturationSteppables import SteadyStateDiffusionSteeringSteppable
instanceOfSteadyStateDiffusionSteeringSteppable=SteadyStateDiffusionSteeringSteppable(sim,_frequency=1)
steppableRegistry.registerSteppable(instanceOfSteadyStateDiffusionSteeringSteppable)

# steering secretion
from DermisMaturationSteppables import SecretionSteeringSteppable
instanceOfSecretionSteeringSteppable=SecretionSteeringSteppable(sim,_frequency=1)
steppableRegistry.registerSteppable(instanceOfSecretionSteeringSteppable)




from DermisMaturationSteppables import PressureAllCells
instanceOfPressureAllCells=PressureAllCells(_simulator=sim,_frequency=10)
steppableRegistry.registerSteppable(instanceOfPressureAllCells)

CompuCellSetup.mainLoop(sim,simthread,steppableRegistry)


# steppables not in use
# # expand lattice
# from DermisMaturationSteppables import DynamicTissueGrowth
# DynamicTissueGrowthSteppableInstance=DynamicTissueGrowth(sim,_frequency=1)
# steppableRegistry.registerSteppable(DynamicTissueGrowthSteppableInstance)





