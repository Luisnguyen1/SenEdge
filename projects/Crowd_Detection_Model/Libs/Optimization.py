# Optimizers

import numpy as np

##################################################################################
####################################### SGD ######################################
##################################################################################
class Optimizer_SGD:

    # Init the optimizer
    # By default, the learning rate is set to 1.0
    
    def __init__(self, learning_rate):
        self.learning_rate = learning_rate

    # Update parameters
    def update_params(self, layer):
        layer.weights += -self.learning_rate * layer.dweights
        layer.biases += -self.learning_rate * layer.dbiases


class Optimizer_SGD_Decay_Momentum:

    # Init the optimizer
    # By default, the learning rate is set to 1.0
    
    def __init__(self, learning_rate, decay, momentum):
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.step = 0
        self.momentum = momentum

    # pre update
    def pre_update_params(self):
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1 / (1 + self.decay * self.step))


    # Update parameters
    def update_params(self, layer):
        if self.momentum:  # if we use momentum
            if not hasattr(layer, 'weights_momentums'):
                # if layers does not contain momentum, create them then fill with zeros
                layer.weights_momentums = np.zeros_like(layer.weights)
                layer.biases_momentums = np.zeros_like(layer.biases)

            # weights update
            weights_updates = self.momentum * layer.weights_momentums - self.current_learning_rate *layer.dweights 
            layer.weights_momentums = weights_updates
            # biaises update
            biases_updates = self.momentum * layer.biases_momentums - self.current_learning_rate *layer.dbiases
            layer.biases_momentums = biases_updates
        else:  # not using momentum
            weights_updates = -self.current_learning_rate * layer.dweights
            biases_updates = -self.current_learning_rate * layer.dbiases

        layer.weights += weights_updates
        layer.biases += biases_updates

    # post update
    def post_update_params(self):
        self.step += 1

##################################################################################
##################################### RMSProp ####################################
##################################################################################

class Optimizer_RMSProp:

    # Init the optimizer
    # By default, the learning rate is set to 1.0
    
    def __init__(self, learning_rate = 0.1, decay = 0., epsilon = 1e-7, rho = 0.5):
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.step = 0
        self.epsilon = epsilon
        self.rho= rho

    # pre update
    def pre_update_params(self):
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1 / (1 + self.decay * self.step))


    # Update parameters
    def update_params(self, layer):
       
        if not hasattr(layer, 'weights_cache'):
            # if layers do not contain momentum, create them then fill with zeros
            layer.weights_cache = np.zeros_like(layer.weights)
            layer.biases_cache = np.zeros_like(layer.biases)

        # weights & biases update
        layer.weights_cache = self.rho * layer.weights_cache + (1-self.rho) * layer.dweights**2 
        layer.biases_cache = self.rho * layer.biases_cache + (1-self.rho) * layer.dbiases**2 
           
        layer.weights += -self.current_learning_rate * layer.dweights / (np.sqrt(layer.weights_cache) + self.epsilon)
        layer.biases += -self.current_learning_rate * layer.dbiases / (np.sqrt(layer.biases_cache) + self.epsilon)

    # post update
    def post_update_params(self):
        self.step += 1

##################################################################################
################################# ADAM ###########################################
##################################################################################

class Optimizer_Adam:

    # Init the optimizer
    # By default, the learning rate is set to 0.1
    
    def __init__(self, learning_rate = 0.1, decay = 5e-3, epsilon = 1e-7, beta1 = 0.9, beta2 = 0.9):
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.step = 0
        self.epsilon = epsilon
        self.beta1 = beta1
        self.beta2= beta2

    # pre update
    def pre_update_params(self):
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1 / (1 + self.decay * self.step))


    # Update parameters
    def update_params(self, layer):
       
        if not hasattr(layer, 'weights_cache'):
            # if layers do not contain momentum, create them then fill with zeros
            layer.weights_momentum = np.zeros_like(layer.weights)
            layer.weights_cache = np.zeros_like(layer.weights)
            layer.biases_momentum = np.zeros_like(layer.biases)
            layer.biases_cache = np.zeros_like(layer.biases)

        # Update momentum with current gradient
        layer.weights_momentum = self.beta1 * layer.weights_momentum + (1 - self.beta1) * layer.dweights
        layer.biases_momentum = self.beta1 * layer.biases_momentum + (1 - self.beta1) * layer.dbiases
        
        # Correct the momentum. step must start with 1 here
        weights_momentum_corrected = layer.weights_momentum / (1 - self.beta1**(self.step +1))
        biases_momentum_corrected = layer.biases_momentum / (1 - self.beta1**(self.step +1))
           
        # update cache
        layer.weights_cache = self.beta2 * layer.weights_cache + (1-self.beta2) * layer.dweights**2 
        layer.biases_cache = self.beta2 * layer.biases_cache + (1-self.beta2) * layer.dbiases**2

        # Obtain the corrected cache
        weights_cache_corrected = layer.weights_cache / (1 - self.beta2**(self.step +1))
        biases_cache_corrected = layer.biases_cache / (1 - self.beta2**(self.step +1))

        # Update weights and biases
        layer.weights += -self.current_learning_rate * weights_momentum_corrected / (np.sqrt(weights_cache_corrected) + self.epsilon)
        layer.biases += -self.current_learning_rate * biases_momentum_corrected / (np.sqrt(biases_cache_corrected) + self.epsilon)
    # post update
    def post_update_params(self):
        self.step += 1

    
        
