import numpy as np
import os
from scipy.interpolate import interp2d
from Tb_PBH_ANN import *
import time
import itertools
from ImportTbPower import *

arrayName = 'hera127'
arrayErr = np.loadtxt('../Sensitivities/NoiseVals_'+arrayName+'.dat')
sensty_arr = interp2d(arrayErr[:,0], arrayErr[:,1], arrayErr[:,2], kind='linear', bounds_error=False, fill_value=1e5)
hlittle = 0.7
tb_analysis = True
GlobalTb = False

Mpbh = 100
Nhidden = 50

Pts_perVar = 10
#fpbh_L = np.logspace(-7, -2, Pts_perVar)
#zetaUV_L = np.linspace(15, 90, Pts_perVar)
#zetaX_L = np.logspace(np.log10(2e55), np.log10(2e57), Pts_perVar)
#Tmin_L = np.logspace(4, 5, Pts_perVar)
#Nalpha_L = np.logspace(np.log10(4e2), np.log10(4e4), Pts_perVar)
k_List = np.logspace(np.log10(0.15), np.log10(1), Pts_perVar)

#Z_list = [8.38, 8.85, 9.34, 9.86, 10.40, 10.97, 11.57, 12.20, 12.86, 13.55,
#          14.28, 15.05, 15.85, 16.69, 17.57, 18.50, 19.48]
fpbh_L = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2]
zetaUV_L = [50]
zetaX_L = [2e55, 2e56, 2e57]
Tmin_L = [5e4]
Nalpha_L = [4e2, 4e3, 4e4]
Z_list = [8.38, 17.57]

totalParmas = float(len(fpbh_L)*len(zetaX_L)*len(zetaUV_L)*len(Tmin_L)*len(Nalpha_L))
cnt = 0

chi2_list = []
param_list = []

modeler = np.zeros(len(Z_list), dtype=object)

error = np.zeros((len(Z_list), len(k_List)))
true_list = np.zeros((len(Z_list), len(k_List)))
for j,zz in enumerate(Z_list):
    initPBH = Tb_PBH_Nnet(Mpbh, globalTb=GlobalTb, HiddenNodes=Nhidden, zfix=zz)
    initPBH.main_nnet()
    initPBH.load_matrix_elems()
    vechold = []
    for i,kk in enumerate(k_List):
        error[j,i] = sensty_arr(zz, kk/hlittle)
        vechold.append([np.log10(kk), -8., np.log10(50), np.log10(2e56), np.log10(5e4), np.log10(4e3)])
    true_list[j,:] = list(itertools.chain.from_iterable(initPBH.rapid_eval(vechold)))
    error[j,:] = np.sqrt(error[j,:]**2. + (0.3*true_list[j,:])**2.)

    modeler[j] = ImportGraph(initPBH.fileN, Mpbh, zz)

for fp in fpbh_L:
    for zUV in zetaUV_L:
        for zX in zetaX_L:
            for Tm in Tmin_L:
                for Na in Nalpha_L:
                    chi2 = 0.
                    param_list.append([fp, zUV, zX, Tm, Na])
                    for j,zz in enumerate(Z_list):
#                        t0 = time.time()                        
                        eval_list = []
                        for i,kk in enumerate(k_List):
                            eval_list.append([np.log10(kk), np.log10(fp), np.log10(zUV), np.log10(zX), np.log10(Tm), np.log10(Na)])
                        val = modeler[j].run_yhat(eval_list)

                        chi2 += np.sum(((val.flatten() - true_list[j,:]) / error[j,:])**2.)
#                        t1 = time.time()
#                        print t1 - t0

                    cnt +=1
                    if cnt%10000 == 0:
                        print 'Finished Run: {:.0f}/{:.0f}'.format(cnt, totalParmas)
                    chi2_list.append(chi2)

chi2_list = np.asarray(chi2_list)
param_list = np.asarray(param_list)
np.savetxt('../Sensitivities/Chi2_Fits_' + arrayName + '_TbPower_Mpbh_{:.0f}_ModerateSense.dat'.format(Mpbh), np.column_stack((param_list, chi2_list)))



