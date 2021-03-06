import os
from Tb_PBH_ANN import *
from Xe_PBH_ANN import *

#Runner for training and testing. Not intended for integration into code. 
Mpbh = 100.

# Train NNet
Train = True
KeepTraining = False
# Load and Evaluate NNet
Eval = False
#Global Tb or power spectrum, or Xe NN
tb_analysis = True
GlobalTb = False

epochs = 10000
HiddenNodes = 50

#redshift = 17.57
#Z_list = [8.38, 8.85, 9.34, 9.86, 10.40, 10.97, 11.57, 12.20, 12.86, 13.55,
#          14.28, 15.05, 15.85, 16.69, 17.57, 18.50, 19.48]
Z_list = [17.57]

fpbh = np.log10(1e-8)
zetaUV = np.log10(50)
zetaX = np.log10(2e56)
Tmin = np.log10(5e4)
Nalpha = np.log10(4e3)

for redshift in Z_list:
    vec_in = [[redshift, fpbh, zetaUV, zetaX, Tmin, Nalpha]]
    if not GlobalTb and tb_analysis:
        k = np.log10(0.1)
        vec_in = [[k, fpbh, zetaUV, zetaX, Tmin, Nalpha]]
    # Evaluate/Run
    if tb_analysis:
        init_pbh = Tb_PBH_Nnet(Mpbh, globalTb=GlobalTb, HiddenNodes=HiddenNodes, epochs=epochs, zfix=redshift)
        init_pbh.main_nnet()
    else:
        init_pbh = Xe_PBH_Nnet(Mpbh, epochs=epochs, HiddenNodes=HiddenNodes)
        init_pbh.main_nnet()

    if Train:
        init_pbh.train_NN(vec_in, keep_training=KeepTraining)
    if Eval:
        init_pbh.eval_NN(vec_in)
