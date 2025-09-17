# Dense Layer - Class definition

import numpy as np

#########################################################################
############################## DENSE  ###################################
#########################################################################

class Dense:

    def __init__(self, n_inputs, n_neurons):
        #init eights and biases
        self.weights = 0.01*np.random.randn(n_inputs,n_neurons)
        self.biases = np.zeros((1,n_neurons))

    def forward(self,inputs):
        #calculate outputs
        self.inputs = inputs
        self.output = np.dot(inputs,self.weights) +self.biases
           
    # backward pass
    def backward(self,dvalues):
        # Gradients on parameters
        self.dweights = np.dot(self.inputs.T, dvalues)
        self.dbiases = np.sum(dvalues, axis = 0, keepdims = True)
        # Gradients on values
        self.dinputs = np.dot(dvalues,self.weights.T)

    def get_parameters(self):
        return self.weights,self.biases
    
    def set_parameters(self,weights,biases):
        self.weights = weights
        self.biases = biases


#########################################################################
################## DENSE with REGULARIZATION L1 L2 ######################
#########################################################################

class Layer_Dense_Regularization:

    def __init__(self, n_inputs, n_neurons, weights_regularizer_l1 = 0, weights_regularizer_l2 = 0, biases_regularizer_l1 = 0, biases_regularizer_l2 = 0):
        # Init eights and biases
        self.weights = 0.01*np.random.randn(n_inputs,n_neurons)
        self.biases = np.zeros((1,n_neurons))
        # Set regularization strength
        self.weights_regularizer_l1 = weights_regularizer_l1
        self.weights_regularizer_l2 = weights_regularizer_l2
        self.biases_regularizer_l1 = biases_regularizer_l1
        self.biases_regularizer_l2 = biases_regularizer_l2

    # forward pass
    def forward(self,inputs):
        #calculate outputs
        self.output = np.dot(inputs,self.weights) + self.biases
        self.inputs = inputs
        
    # backward pass
    def backward(self,dvalues):
        # Gradients on parameters
        self.dweights = np.dot(self.inputs.T, dvalues)
        self.dbiases = np.sum(dvalues, axis = 0, keepdims = True)

        # Gradients on regularization
        # L1 on weights
        if (self.weights_regularizer_l1 > 0):
            dL1 = np.ones_like(self.weights)   # return an array filled of 1, same shape as weights array
            dL1[self.weights < 0] = -1
            self.dweights += self.weights_regularizer_l1 * dL1

        # L2 on weights
        if (self.weights_regularizer_l1 > 0):
            self.dweights += 2 * self.weights_regularizer_l2 * self.weights

        # L1 on biases
        if (self.biases_regularizer_l1 > 0):
            dL1 = np.ones_like(self.biases)   # return an array filled of 1, same shape as biases array
            dL1[self.biases < 0] = -1
            self.dbiases += self.biases_regularizer_l1 * dL1

        # L2 on biases
        if (self.biases_regularizer_l1 > 0):
            self.dbiases += 2 * self.biases_regularizer_l2 * self.biases

        # Gradients on values
        self.dinputs = np.dot(dvalues,self.weights.T)

    def get_parameters(self):
        return self.weights,self.biases
    
    def set_parameters(self,weights,biases):
        self.weights = weights
        self.biases = biases

#########################################################################
############################  DROP OUT Layer ############################
#########################################################################

class Dense_Dropout:

    def __init__(self, rate):
        self.rate = 1 - rate  # invert the rate

    # forward pass
    def forward(self,inputs):
       self.inputs  = inputs
       
       # generate a scaled mask
       self.binary_mask = np.random.binomial(1, self.rate, size = inputs.shape) / self.rate
       
       # Compute the output value
       self.output = inputs * self.binary_mask
        
    # backward pass
    def backward(self,dvalues):
        self.dinputs = dvalues * self.binary_mask