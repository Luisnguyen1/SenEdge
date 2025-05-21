# Class Cross Entropy Loss

import numpy as np
import math

# Loss Class
class Loss:

    # Set Remember Trainable Layer
    def remember_trainable_layers(self, trainable_layers):
        self.trainable_layers = trainable_layers

    # Calculate the data and regulazation losses given
    # the output and the ground truth values
    def calculate(self,output,y, *, include_regularization = False):
        #Calculate sample losses:
        sample_losses = self.forward(output,y)
        #Calculate mean loss:
        data_loss = np.mean(sample_losses)

        if not include_regularization:
            return data_loss
        
        #Return loss:
        return data_loss, self.regularization_loss() 
    
    # Regularization
    def regularization_loss(self):
        # set regularization to 0 by default
        regularization_loss = 0

        for layer in self.trainable_layers:
            # Calculate L1_regularization for weights
            if (layer.weights_regularizer_l1 > 0):
                regularization_loss += layer.weights_regularizer_l1 * np.sum(np.abs(layer.weights))

            # Calculate L2_regularization for weights
            if (layer.weights_regularizer_l2 > 0):
                regularization_loss += layer.weights_regularizer_l2 * np.sum(layer.weights**2)

            # Calculate L1_regularization for biases
            if (layer.biases_regularizer_l1 > 0):
                regularization_loss += layer.biases_regularizer_l1 * np.sum(np.abs(layer.biases))

            # Calculate L2_regularization for biases
            if (layer.biases_regularizer_l2 > 0):
                regularization_loss += layer.biases_regularizer_l2 * np.sum(layer.biases**2)

        return regularization_loss
    
     # Forward Pass
    def forward(self, y_pred, y_true):
        # Calculate loss
        sample_losses = np.mean((y_true - y_pred)**2, axis = -1)  # axis = -1 represents the last axis
        return sample_losses


    # Backward Pass
    def backward(self, dvalues, y_true):
        # Determine the number of samples
        samples = len(dvalues)

        # number of outputs in every sample, here we use the first sample to count
        outputs = len(dvalues[0])

        # Calculate gradient
        self.dinputs = -2 * (y_true - dvalues) / outputs
        
        # Normalize gradient
        self.dinputs = self.dinputs / samples

# Cross Entropy Loss Class
class Loss_CategoricalCrossentropy(Loss): 

    # Forward Pass
    def forward(self, y_pred, y_true):
        samples = len(y_pred)

        # Clip both sides to not drag mean toward any values
        y_pred_clipped = np.clip(y_pred,1e-7,1-1e-7) #1e-7 is added to avoid division by 0

        # Probabilities for target values only if categorical labels

        if len(y_true.shape) == 1: # The array is 1D
            correct_confidence = y_pred_clipped[
                range(samples),
                y_true
            ]
        elif len(y_true.shape) == 2: # The array is 2D
            correct_confidence = np.sum(
                y_pred_clipped*y_true,
                axis = 1
            )

        # Losses calculation
        negative_log_likelihoods = -np.log(correct_confidence)
        return negative_log_likelihoods

    # Backward Pass
    def backward(self, dvalues, y_true):
        # Determine the number of samples
        samples = len(dvalues)
        # Determine the number of labels in each sample
        # We use the first sample to count
        labels = len(dvalues[0])

        # if labels are sparse, turn them into one vector
        if len(y_true.shape) == 1:
            y_true = np.eye(labels)[y_true]

        # Calculate gradient
        self.dinputs = - y_true / dvalues
        # Normalize gradient
        self.dinputs = self.dinputs / samples

    # Regularization
    def regularization_loss(self, layer):
        # set regularization to 0 by default
        regularization_loss = 0
        for layer in self.trainable_layers:
            # Calculate L1_regularization for weights
            if (layer.weights_regularizer_l1 > 0):
                regularization_loss += layer.weights_regularizer_l1 * np.sum(np.abs(layer.weights))

            # Calculate L2_regularization for weights
            if (layer.weights_regularizer_l2 > 0):
                regularization_loss += layer.weights_regularizer_l2 * np.sum(layer.weights**2)

            # Calculate L1_regularization for biases
            if (layer.biases_regularizer_l1 > 0):
                regularization_loss += layer.biases_regularizer_l1 * np.sum(np.abs(layer.biases))

            # Calculate L2_regularization for biases
            if (layer.biases_regularizer_l2 > 0):
                regularization_loss += layer.biases_regularizer_l2 * np.sum(layer.biases**2)

        return regularization_loss

# MSE Loss Class
class Loss_MeanSquaredError(Loss): 

    # Forward Pass
    def forward(self, y_pred, y_true):
        # Calculate loss
        sample_losses = np.mean((y_true - y_pred)**2, axis = -1)  # axis = -1 represents the last axis
        return sample_losses
        
    # Backward Pass
    def backward(self, dvalues, y_true):
        # Determine the number of samples
        samples = len(dvalues)

        # number of outputs in every sample, here we use the first sample to count
        outputs = len(dvalues)

        # Calculate gradient 
        self.dinputs = -2 * (y_true - dvalues) / outputs
        #dx = dx / samples
        #self.dinputs = np.array([dx,np.zeros(len(dx))]).T
        #self.dinputs = np.array([dx,dx]).T

        # Normalize gradient
        self.dinputs = self.dinputs / samples

    # Regularization
    def regularization_loss(self, layer):
        # set regularization to 0 by default
        regularization_loss = 0

        for layer in self.trainable_layers:
            # Calculate L1_regularization for weights
            if (layer.weights_regularizer_l1 > 0):
                regularization_loss += layer.weights_regularizer_l1 * np.sum(np.abs(layer.weights))

            # Calculate L2_regularization for weights
            if (layer.weights_regularizer_l2 > 0):
                regularization_loss += layer.weights_regularizer_l2 * np.sum(layer.weights**2)

            # Calculate L1_regularization for biases
            if (layer.biases_regularizer_l1 > 0):
                regularization_loss += layer.biases_regularizer_l1 * np.sum(np.abs(layer.biases))

            # Calculate L2_regularization for biases
            if (layer.biases_regularizer_l2 > 0):
                regularization_loss += layer.biases_regularizer_l2 * np.sum(layer.biases**2)

        return regularization_loss