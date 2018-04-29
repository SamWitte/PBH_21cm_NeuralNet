import numpy as np
import os
from scipy.interpolate import interp2d
from Xe_PBH_ANN import *
import time
import itertools

Mpbh = 100
Nhidden = 50

xefactor = 1.07942599999999

Pts_perVar = 2
fpbh_L = np.logspace(-7, -2, Pts_perVar)
zetaUV_L = np.linspace(15, 90, Pts_perVar)
zetaX_L = np.logspace(np.log10(2e55), np.log10(2e57), Pts_perVar)
Tmin_L = np.logspace(4, 5, Pts_perVar)
Nalpha_L = np.logspace(np.log10(4e2), np.log10(4e4), Pts_perVar)
k_List = np.logspace(np.log10(0.1), np.log10(2), Pts_perVar)
Z_list = np.linspace(6, 30, 200)

totalParmas = Pts_perVar**5
cnt = 0

for fp in fpbh_L:
    for zUV in zetaUV_L:
        for zX in zetaX_L:
            for Tm in Tmin_L:
                for Na in Nalpha_L:
                    initPBH = initPBH = Xe_PBH_Nnet(Mpbh,HiddenNodes=Nhidden)
                    initPBH.main_nnet()
                    initPBH.load_matrix_elems()
                    eval_list = []
                    for j,zz in enumerate(Z_list):
                        eval_list.append([zz, np.log10(fp), np.log10(zUV), np.log10(zX), np.log10(Tm), np.log10(Na)])

                    val = initPBH.rapid_eval(eval_list).flatten()
                    val = np.asarray(val)
                    val[val > xefactor] = xefactor
                    maxZ = np.argmax(val)
                    val[:maxZ] = val[maxZ]
                    sve_info = np.column_stack((Z_list, val))
                    fileN = 'nn_xe_files/XeHistory_Mpbh_{:.0e}_fpbh_{:.1e}_zetaUV_{:.2e}_zetaX_{:.2e}_Tmin_{:.2e}_Nalpha_{:.2e}.dat'.format(Mpbh,fp,zUV,zX,Tm,Na)
                    np.savetxt(fileN, sve_info)

                    cnt +=1
                    if cnt%10000 == 0:
                        print 'Finished Run: {:.0f}/{:.0f}'.format(cnt, totalParmas)
