def rssi_to_distance(rssi, tx_power=-59):
    if rssi == 0:
        return -1  # if we cannot determine the distance, return -1
    ratio = rssi * 1.0 / tx_power
    if ratio < 1.0:
        return 10 ** ((tx_power - rssi) / 20)
    else:
        return 0.89976 * (10 ** ((tx_power - rssi) / 10)) + 0.11173