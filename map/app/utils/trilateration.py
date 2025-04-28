def trilaterate(beacons):
    if len(beacons) < 3:
        raise ValueError("At least three beacons are required for trilateration.")

    # Extracting the beacon positions and distances
    positions = [(b['x'], b['y']) for b in beacons]
    distances = [b['d'] for b in beacons]

    # Using the trilateration formula
    A = 2 * (positions[1][0] - positions[0][0])
    B = 2 * (positions[1][1] - positions[0][1])
    C = distances[0]**2 - distances[1]**2 - positions[0][0]**2 + positions[1][0]**2 - positions[0][1]**2 + positions[1][1]**2
    D = 2 * (positions[2][0] - positions[1][0])
    E = 2 * (positions[2][1] - positions[1][1])
    F = distances[1]**2 - distances[2]**2 - positions[1][0]**2 + positions[2][0]**2 - positions[1][1]**2 + positions[2][1]**2

    # Solving the linear equations
    x = (C - F * B / E) / (A - D * B / E)
    y = (C - A * x) / B

    return {'x': x, 'y': y}