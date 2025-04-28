function computePosition(adData) {
  // adData: [{uuid, rssi}]
  const beacons = adData.map(a => ({ ...a, d: rssiToDistance(a.rssi) }));
  const top3 = beacons.sort((a,b) => a.d - b.d).slice(0, 3);
  let { x, y } = trilaterate(top3);
  x = KalmanFilter('x').filter(x);
  y = KalmanFilter('y').filter(y);
  return { x, y };
}