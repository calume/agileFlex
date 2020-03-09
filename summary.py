import pandas as pd

def summary(LoadsIn,Violperphase,CurMax, Vmax, Vmin,PN,Gen,PO,LB,UB):
    Coords = pd.read_csv("XY_Position.csv")
    LoadBusByPhase={}   
    tol=0.0000    
    for p in range(0,3):
        LoadBus=pd.DataFrame(columns=(['Bus','Phase','X','Y']))
        LoadBus['Bus']=LoadsIn['Bus1'].str[5:-2]
        LoadBus['Phase']=LoadsIn['Bus1'].str[-1:]
        for i in range(0,len(LoadBus)):
           LoadBus['X'][i]=float(Coords['X'][int(LoadBus['Bus'][i])==Coords['Node']].values)
           LoadBus['Y'][i]=float(Coords['Y'][int(LoadBus['Bus'][i])==Coords['Node']].values)
           ######## Create Summary Sheets #############
        
        if Vmax[:,p] > 1.1:
            LoadBus['VMax-Dem-UP'] = Violperphase[p]['VmaxPercPercUp'].round(4)
            LoadBus['VMax-Dem-DOWN'] = Violperphase[p]['VmaxPercPercDown'].round(4)
        if Vmin[:,p] < 0.94:
            LoadBus['VMin-Dem-DOWN'] = Violperphase[p]['VminPercPercDown'].round(4)
            LoadBus['VMin-Dem-UP'] = Violperphase[p]['VminPercPercUp'].round(4)              
        if CurMax[:,p] > 0.5:
            LoadBus['Cmax-Dem-UP'] = Violperphase[p]['CurPercPercUp'].round(4)
            LoadBus['Cmax-Dem-DOWN'] = Violperphase[p]['CurPercPercDown'].round(4)
           
        LoadBus['Action']='NA'
           
        for i in range(0,len(LoadBus)):
           ###### Cmax Adjustments ##########
           if CurMax[:,p] > 0.5:
              if LoadBus['Cmax-Dem-DOWN'][i] < -tol:
                 LoadBus['Action'][i]='C-'#(Cmax)' 
              if LoadBus['Cmax-Dem-UP'][i] < -tol:
                 LoadBus['Action'][i]='C+'#(Cmax)' 
           
           ####### Vmax and Vmin Adjustments #########
           if Vmin[:,p] < 0.94:
              if LoadBus['VMin-Dem-UP'][i] > tol:
                 LoadBus['Action'][i]='VL+'#(Vmin)' 
              if LoadBus['VMin-Dem-DOWN'][i] > tol:
                 LoadBus['Action'][i]='VL-'#(Vmin)' 
             
           if Vmax[:,p] > 1.1:   
              if LoadBus['VMax-Dem-DOWN'][i] < -tol:
                 LoadBus['Action'][i]='VU-'#(Vmax)'
              if LoadBus['VMax-Dem-UP'][i] < -tol:
                 LoadBus['Action'][i]='VL+'#(Vmax)'
           
           
           ####### Combined #########
           if Vmax[:,p] > 1.1 and CurMax[:,p] > 0.5:
              if LoadBus['VMax-Dem-UP'][i] < -tol and LoadBus['Cmax-Dem-UP'][i] < -tol:
                 LoadBus['Action'][i]='C/VU+'#+(Vmax/Cmax)' 
              if LoadBus['VMax-Dem-DOWN'][i] < -tol and LoadBus['Cmax-Dem-DOWN'][i] < -tol:
                 LoadBus['Action'][i]='C/VU-'#+(Vmax/Cmax)'              
           if Vmin[:,p] < 0.94 and CurMax[:,p] > 0.5:
              if LoadBus['VMin-Dem-DOWN'][i] > tol and LoadBus['Cmax-Dem-DOWN'][i] < -tol:
                 LoadBus['Action'][i]='VL/C-'#(Vmin/Cmax)'
              if LoadBus['VMin-Dem-UP'][i] > tol and LoadBus['Cmax-Dem-UP'][i] < -tol:
                 LoadBus['Action'][i]='VL/C+'#(Vmin/Cmax)'
                   
           if Vmin[:,p] < 0.94 and Vmax[:,p] > 1.1: 
              if LoadBus['VMax-Dem-DOWN'][i] < -tol and LoadBus['VMin-Dem-DOWN'][i] > tol:
                 LoadBus['Action'][i]='VU/VL-'#-(Vmax/Vmin)'
              if LoadBus['VMax-Dem-UP'][i] < -tol and LoadBus['VMin-Dem-UP'][i] > tol:
                 LoadBus['Action'][i]='VU/VL+'#(Vmax/Vmin)'
                    
           if Vmin[:,p] < 0.94 and Vmax[:,p] > 1.1 and CurMax[:,p] > 0.5: 
              if LoadBus['VMax-Dem-DOWN'][i] < -tol and LoadBus['VMin-Dem-DOWN'][i] > tol and LoadBus['Cmax-Dem-DOWN'][i] < -tol:
                 LoadBus['Action'][i]='VU/VL/C-'#-(Vmax/Vmin)'
              if LoadBus['VMax-Dem-UP'][i] < -tol and LoadBus['VMin-Dem-UP'][i] > tol and LoadBus['Cmax-Dem-UP'][i] < -tol:
                 LoadBus['Action'][i]='VU/VL/C+'#(Vmax/Vmin)'
        LoadBus['DemandSP'] = PO
        LoadBus['NewSP']=PN
        LoadBus['Adjust']=PO-PN
        LoadBus['UB']=UB
        LoadBus['LB']=LB
        LoadBus['UHDRm']=Gen-UB
        LoadBus['LHDRm']=PN-LB
        LoadBus=LoadBus[LoadBus['Phase'].astype(int)==(p+1)]
        LoadBusByPhase[p] = LoadBus
    return LoadBusByPhase
    
