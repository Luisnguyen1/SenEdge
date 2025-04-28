from pykalman import KalmanFilter

class KalmanFilterWrapper:
    def __init__(self):
        self.kf = KalmanFilter(initial_state_mean=0, n_dim_obs=1)
        self.kf = self.kf.em(1, n_iter=10)

    def filter(self, measurements):
        return self.kf.smooth(measurements)