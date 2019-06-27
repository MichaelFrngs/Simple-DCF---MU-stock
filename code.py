import pandas as pd
import os
import datetime as dt
import pandas_datareader.data as web
import time

os.chdir("C:/Users/mfrangos2016/Desktop/MU")

#Load up financial statements
BS = pd.DataFrame(pd.read_csv("bs.csv"))
IS = pd.DataFrame(pd.read_csv("is.csv"))
CF = pd.DataFrame(pd.read_csv("cf.csv"))

#SET PARAMETERS HERE
#From zero to 1, how certain are you about getting the projected free cash flows?
FCFgrowth_discount_factor =  1
#conformance to us longterm gdp growth
terminal_growth = 0.028
years_to_project = 5
WACC = .1





#Set row index
BS = BS.rename(index=BS[BS.columns[0]]).iloc[:,[1,2,3]]
IS = IS.rename(index=IS[IS.columns[0]]).iloc[:,[1,2,3]]
CF = CF.rename(index=CF[CF.columns[0]]).iloc[:,[1,2,3]]

date = dt.datetime.now()
#Live price!
price = web.DataReader("MU", 'yahoo', dt.datetime(date.year,date.month,date.day),dt.datetime(date.year,date.month,date.day) ).reset_index()  
sharesOutstanding = 1134255375/1000000

marketCap = price.iloc[0][4] * sharesOutstanding
print("Live Market Cap = ",marketCap/1000, "Billion")

#DCF
def calc_Historical_FCF():
    EBIT = IS.loc["Operating income"]
    Taxes = .21*EBIT
    Depreciation = CF.iloc[3]
    
    ChngNWC = pd.DataFrame(columns=CF.columns,index = [1])
    for column in CF.columns:
        #print(column)
        ChngNWC[column] = sum(CF[9:15][column])
    #print("Change in NWC = ",ChngNWC)
            
    Capex = CF.loc["Expenditures for property, plant, and equipment"]
    
    FCF = EBIT - Taxes + Depreciation + ChngNWC + Capex
    #print("Historical FCF = ", FCF)
    return FCF

#Average historical CAGR
def calculate_FCF_Expcted_growth(FCFgrowth_discount_factor, FCF = calc_Historical_FCF()):
    last_position = (len(FCF.iloc[0,:])-1)
    final_year = FCF.iloc[0,last_position]
    first_year = FCF.iloc[0,0]
    numHistoricalYears = len(FCF.iloc[0,:])
    
    count = 0
    while first_year <0:
        count= count+1
        first_year = FCF.iloc[0,count]
        #print(f"Error using first historical FCF for estimating growth. Using next year.Count:{count}")
        time.sleep(1)
        if count > (numHistoricalYears-1):
            print("Error getting average historical FCF growth rate. Probably too many negative numbers")
            break
    #print("Growth Rate Estimate from historicals = ", ((final_year / first_year )**(1/(numHistoricalYears-1-count))-1))
    return ((final_year / first_year )**(1/(numHistoricalYears-1-count))-1)*FCFgrowth_discount_factor
    

def projection_years(years_2_project):
    ProjectionYears = []
    for i in range(years_2_project):
        ProjectionYears.append(i+1)
    return ProjectionYears

#PROJECT CASH FLOWS
def calc_trminalValue_and_FFCF(years_2_project,
                      FCF = calc_Historical_FCF()
                      ):
    import math
    FFCF = pd.DataFrame(columns=projection_years(years_2_project),index = [1])
    for column in FFCF.columns:
        #if first column is empty
        if math.isnan(FFCF.iloc[0,0]):
            #final year * (1+growth)
            FFCF[column] = FCF.iloc[0,-1]*(1+calculate_FCF_Expcted_growth(FCFgrowth_discount_factor))
        else:   
            FFCF[column] = FFCF[column-1]*(1+calculate_FCF_Expcted_growth(FCFgrowth_discount_factor))
    Terminal_Value = FFCF[column]*(1+terminal_growth)/(WACC - terminal_growth)
    #print("Terminal_Value = ",Terminal_Value) 
    #print("In calc...._FFCF(), FFCFs = ",FFCF)
    return Terminal_Value, FFCF

def discount(data,ProjectionYears,WACC_):
    print("For discount function, WACC is = ",WACC_)
    tempvar = pd.DataFrame(columns=ProjectionYears,index = [1])
    iterations = len(data.iloc[0,:])
    i=0
    while i < iterations:
        print("Discounting... FFCF# ", i+1)
        tempvar.iloc[0,i] = data.iloc[0,i]/(1+WACC_)**(i+1)
        i=i+1
    return tempvar

def calculate_Intrinsic_Value(years_2_project,    
                              WACC_,
                              HFCF = calc_Historical_FCF(), 
                              Terminal_Value = calc_trminalValue_and_FFCF(years_2_project = years_to_project)[0],
                              FFCF = calc_trminalValue_and_FFCF(years_2_project = years_to_project)[1],
                              ):   
    print("While calculating Intrinsic value, historicals FCF = ", HFCF)                             
    print("WACC =", WACC_)
    DiscountedFCFs = discount(FFCF, projection_years(years_2_project), WACC_)
    print(":::::::::::::::::DiscountedFCFs:::::::::::::\n", DiscountedFCFs)
    
    EnterpriseValue = DiscountedFCFs.sum(axis=1) + Terminal_Value/(1+WACC_)**years_2_project
    print("EnterpriseValue = ", EnterpriseValue)
    
    FirmValue = EnterpriseValue + BS.loc["Cash and equivalents"][len(BS.iloc[0,:])-1] 
    FirmValue = FirmValue + BS.loc["Long-term marketable investments"][len(BS.iloc[0,:])-1]
    FirmValue = FirmValue + BS.loc["Short-term investments"][len(BS.iloc[0,:])-1]
    print("FirmValue = ", FirmValue)
    
    EquityValue = FirmValue - BS.loc["Long-term debt"][len(BS.iloc[0,:])-1]
    EquityValue = EquityValue - BS.loc["Noncontrolling interests in subsidiaries"][len(BS.iloc[0,:])-1]
    
    IntrinsicValue = EquityValue/sharesOutstanding
    print("IntrinsicValuePerShare  =", IntrinsicValue, "\n")
    print("Upside =",int((IntrinsicValue/price.iloc[0][4])*100),"%")
    
calculate_Intrinsic_Value(WACC_ = WACC, years_2_project = years_to_project)
