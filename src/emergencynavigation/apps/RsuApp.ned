package emergencynavigation.apps;

import emergencynavigation.apps.EmergencyRelayApp;

simple RsuApp extends EmergencyRelayApp
{
    @class(emergencynavigation::RsuApp);
    @display("i=block/app2");
    bool accidentDetector = default(false);
    double accidentTime @unit(s) = default(60s);
    double stoppedSeconds @unit(s) = default(3s);
    string accidentVehicleId = default("accident");
    string accidentRoad = default("D3C3");
    int payloadBytes = default(256);
}
