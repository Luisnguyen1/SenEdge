
import numpy as np
import math

class Accuracy:
    def calculate(self, predictions, y):
        
        comparisons = self.compare(predictions,y)
        accuracy = np.mean(comparisons)
        
        return accuracy
    
class Accuracy_Regression(Accuracy):
    def __init__(self):
        self.precision = None

    def init(self, y, reinit = False):
        if self.precision is None or reinit:
            self.precision = np.std(y) / 250

    def compare(self, predictions, y):
        return np.absolute(predictions - y) < self.precision

class Accuracy_Categorical(Accuracy):
    def init(self,y):
        pass   # no need to init

    def compare(self, predictions, y):
        output = predictions 
        predictions = np.argmax(output, axis = 1)
        if len(y.shape) == 2:
            y = np.argmax(y, axis = 1)
        return np.mean(predictions == y)