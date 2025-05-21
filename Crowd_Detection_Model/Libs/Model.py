import numpy as np
import math
import pickle

# Create an class Input Layer to execute a Forward Pass
class Input_Layer:
    # Just perform a forward pass
    def forward(self, inputs):
        self.output = inputs

# Class Model
class Model:

    def __init__(self):
        # Create an empty list of layers
        self.layers = []

    def add(self,layer):
        self.layers.append(layer)


    def set(self, *, loss, optimizer, accuracy):
    #def set(self, *, optimizer):
        self.loss = loss
        self.optimizer = optimizer
        self.accuracy = accuracy

    def finalize(self):
        # Create an input layer
        self.input_layer = Input_Layer()

        # Count the number of layers in the model:
        layers_count = len(self.layers)

        # Init the list of trainable layers:
        self.trainable_layers = []

        for i in range(layers_count):
            if i==0:
                self.layers[i].previous = self.input_layer
                self.layers[i].next = self.layers[i+1]
            elif i < (layers_count-1):
                self.layers[i].previous = self.layers[i-1]
                self.layers[i].next = self.layers[i+1]
            else:
                self.layers[i].previous = self.layers[i-1]
                self.layers[i].next = self.loss
                self.output_layer_activation = self.layers[i]

            if hasattr(self.layers[i],'weights'):
                self.trainable_layers.append(self.layers[i])

        # Update loss object with trainable layers
        self.loss.remember_trainable_layers(self.trainable_layers)

    def forward(self, X):
        #perform the forward pass in the model
        self.input_layer.forward(X)

        for layer in self.layers:
            layer.forward(layer.previous.output)

        return layer.output

    def backward(self, output, y):
        self.loss.backward(output,y)

        for layer in reversed(self.layers):
            layer.backward(layer.next.dinputs)
        

    def train(self, X, y, validation_data, epochs=1, print_every=1):
        
        self.accuracy.init(y)
    
        # Main training loop
        for epoch in range(1, epochs+1):
            output = self.forward(X)

            # Calculate loss
            data_loss, regularization_loss = self.loss.calculate(output,y, include_regularization = True)
            loss = data_loss + regularization_loss
            #data_loss= self.loss.calculate(output,y, include_regularization = False)
            loss = data_loss 

            # Calculate predictions and accuracy
            predictions = self.output_layer_activation.predictions(output)
            accuracy = self.accuracy.calculate(predictions,y)
        
            self.backward(output,y)

            # Optimize parameters
            self.optimizer.pre_update_params()
            for layer in self.trainable_layers:
                self.optimizer.update_params(layer)
            self.optimizer.post_update_params()

            if not epoch % print_every:
                print(f'epoch: {epoch},  ' + 
                    f'acc: {accuracy:.3f},  ' +
                    f'loss: {loss:.3f},  ' +
                    f'LR: {self.optimizer.current_learning_rate}3f')

        # if there is a validation data:
        if validation_data is not None:
            output = self.forward(validation_data[0])
            loss = self.loss.calculate(output,validation_data[1],include_regularization = False)
            predictions = self.output_layer_activation.predictions(output)
            accuracy = self.accuracy.calculate(predictions,validation_data[1])

            print(f'validation, ' + f'accuracy:{accuracy:.3f}, ' + f'loss:{loss:.3f}')

    def get_parameters(self):
        parameters = []
        for layer in self.trainable_layers:
            parameters.append(layer.get_parameters())
        return parameters
    
    def set_parameters(self, parameters):
        for parameters_set, layer in zip(parameters,self.trainable_layers):
            layer.set_parameters(*parameters_set)

    def save_parameters(self,path):
        # Open a file in the binary write mode and save parameters to it
        with open(path,'wb') as f:
            pickle.dump(self.get_parameters(),f)

    def load_parameters(self,path):
        # Open a file in the binary write mode and load its parameters
        with open(path,'rb') as f:
            self.set_parameters(pickle.load(f))

