import tensorflow as tf
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import os
import itertools
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

RANDOM_SEED = 42
tf.set_random_seed(RANDOM_SEED)

class Xe_PBH_Nnet(object):
    def __init__(self, mPBH, epochs=10000, HiddenNodes=30):
        tf.reset_default_graph()
        self.mPBH = mPBH
        self.h_size = HiddenNodes
        
        self.N_EPOCHS = epochs
        self.grad_stepsize = 1e-3
       
        self.dirName = 'MetaGraphs/Xe_PBH_Mass_{:.0e}_Power'.format(self.mPBH)
        self.fileN = self.dirName + '/PBH21cm_Graph_Mpbh_{:.0e}'.format(self.mPBH)
        self.errThresh = -1.
        if not os.path.exists(self.dirName):
            os.mkdir(self.dirName)
    
    def init_weights(self, shape):
        """ Weight initialization """
        stddev = 0.1
        weights = tf.random_normal(shape, stddev=stddev)
        return tf.Variable(weights)

    def forwardprop(self, X, w_1, w_2, w_3):
        """
        Forward-propagation.
        """
        hid1 = tf.nn.sigmoid(tf.matmul(X, w_1))
        hid2 = tf.nn.sigmoid(tf.matmul(hid1, w_2))
        yhat = tf.matmul(hid2, w_3)
        return yhat

    def get_data(self, frac_test=0.25):
        self.scalar = StandardScaler()
       
        fileNd = '../XeFiles/XeFull_Mpbh_{:.0e}.dat'.format(self.mPBH)
        inputN = 6
        tbVals = np.loadtxt(fileNd)
        np.random.shuffle(tbVals)
        data = tbVals[:, :inputN]
        target = tbVals[:, inputN:]
        target = np.log10(target)
        dataSTD = self.scalar.fit_transform(data)
    
        self.train_size = (1.-frac_test)*len(tbVals[:,0])
        self.test_size = frac_test*len(tbVals[:,0])
        # Prepend the column of 1s for bias
        N, M  = data.shape
        all_X = np.ones((N, M + 1))
        all_X[:, 1:] = dataSTD
        
        return train_test_split(all_X, target, test_size=frac_test, random_state=RANDOM_SEED)

    def main_nnet(self):#, train_nnet=True, eval_nnet=False, evalVec=[], keep_training=False):
        
        self.train_X, self.test_X, self.train_y, self.test_y = self.get_data()
        self.err_train = np.zeros_like(self.train_y)
        self.err_test = np.zeros_like(self.test_y)
        for i in range(len(self.err_train)):
            if self.train_y[i] < self.errThresh:
                self.err_train[i] = self.errThresh
            else:
                self.err_train[i] = self.train_y[i]
        for i in range(len(self.err_test)):
            if self.test_y[i] < self.errThresh:
                self.err_test[i] = self.errThresh
            else:
                self.err_test[i] = self.test_y[i]

        # Layer's sizes
        self.x_size = self.train_X.shape[1]   # Number of input nodes: [z, k?, fpbh, zeta_UV, zetaX, tmin, nalpha]
        self.y_size = self.train_y.shape[1]   # Value of xe

        # Symbols
        self.X = tf.placeholder("float", shape=[None, self.x_size])
        self.y = tf.placeholder("float", shape=[None, self.y_size])

        # Weight initializations
        self.w_1 = self.init_weights((self.x_size, self.h_size))
        self.w_2 = self.init_weights((self.h_size, self.h_size))
        self.w_3 = self.init_weights((self.h_size, self.y_size))

        # Forward propagation
        self.yhat = self.forwardprop(self.X, self.w_1, self.w_2, self.w_3)
        
        # Backward propagation
        self.cost = tf.reduce_sum(tf.square((self.y - self.yhat), name="cost"))
        self.updates = tf.train.GradientDescentOptimizer(self.grad_stepsize).minimize(self.cost)
        
        # Error Check
#        self.perr_train = tf.reduce_sum(tf.abs((self.y - self.yhat)/self.err_train))
#        self.perr_test = tf.reduce_sum(tf.abs((self.y - self.yhat)/self.err_test))
        self.perr_train = tf.reduce_sum(tf.abs((10.**self.y - 10.**self.yhat)/10.**self.err_train))
        self.perr_test = tf.reduce_sum(tf.abs((10.**self.y - 10.**self.yhat)/10.**self.err_test))

        self.saveNN_Xe = tf.train.Saver()

        return

    def train_NN(self, evalVec, keep_training=False):
        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            if keep_training:
                self.saveNN_Xe.restore(sess, self.fileN)
                print 'Model Restored.'
            BATCH_SIZE = 20
            train_count = len(self.train_X)
            for i in range(1, self.N_EPOCHS + 1):
                for start, end in zip(range(0, train_count, BATCH_SIZE),
                                      range(BATCH_SIZE, train_count + 1,BATCH_SIZE)):
                    sess.run(self.updates, feed_dict={self.X: self.train_X[start:end],
                                                   self.y: self.train_y[start:end]})

                if i % 100 == 0:
                    train_accuracy = sess.run(self.perr_train, feed_dict={self.X: self.train_X, self.y: self.train_y})
                    test_accuracy = sess.run(self.perr_test, feed_dict={self.X: self.test_X, self.y: self.test_y})
                    print("Epoch = %d, train accuracy = %.7e, test accuracy = %.7e"
                          % (i + 1, train_accuracy/len(self.train_X), test_accuracy/len(self.test_X)))
                    
                    predictions = sess.run(self.yhat, feed_dict={self.X: np.insert(self.scalar.transform(evalVec), 0, 1., axis=1)})
                    print 'Current Predictions: ', predictions
            self.saveNN_Xe.save(sess, self.fileN)
        return

    def eval_NN(self, evalVec):
        with tf.Session() as sess:
           
            saverMeta = tf.train.import_meta_graph(self.fileN + '.meta')
            self.saveNN_Xe.restore(sess, self.fileN)
            predictions = sess.run(self.yhat, feed_dict={self.X: np.insert(self.scalar.transform(evalVec), 0, 1., axis=1)})
        
        return np.power(10, predictions)

    def load_matrix_elems(self):
        with tf.Session() as sess:
            self.saveNN_Xe.restore(sess, self.fileN)
            self.Matrix1 = sess.run(self.w_1)
            self.Matrix2 = sess.run(self.w_2)
            self.Matrix3 = sess.run(self.w_3)
        return

    def rapid_eval(self, evalVec):
        inputV = np.insert(self.scalar.transform(evalVec), 0, 1., axis=1)
        h1 = self.sigmoid(np.matmul(inputV, self.Matrix1))
        h2 = self.sigmoid(np.matmul(h1, self.Matrix2))
        predictions = np.matmul(h2, self.Matrix3)
        return np.power(10, predictions)

    def sigmoid(self, x):
        return 1/(1+np.exp(-x))

