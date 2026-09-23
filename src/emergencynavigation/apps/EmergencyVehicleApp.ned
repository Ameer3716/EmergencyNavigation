package emergencynavigation.apps;

import emergencynavigation.apps.EmergencyRelayApp;

simple EmergencyVehicleApp extends EmergencyRelayApp
{
    @class(emergencynavigation::EmergencyVehicleApp);
    @display("i=block/app2");
    string roadNetworkFile = default("grid.net.xml");
    string destinationEdge = default("D2D3");
    bool dynamicRouting = default(false);
    string routingMode = default("mist_static");
    bool forceMistFailure = default(false);
    double watchdogThreshold @unit(s) = default(800ms);
    string nearestFogRsu = default("EmergencyGridScenario.rsu[0]");
    string fallbackLogPath = default("../../artifacts/logs/fallback-events.csv");
    bool preemptionEnabled = default(true);
    double preemptionCheckInterval @unit(s) = default(500ms);
    double preemptionDistance @unit(m) = default(250m);
    double preemptionEta @unit(s) = default(15s);
    double navigationHoldTime @unit(s) = default(64s);
    double releaseSpeed @unit(mps) = default(13.9mps);
    double dynamicUpdateInterval @unit(s) = default(5s);
    double congestionSpeedThreshold = default(0.3);
    double minimumRouteImprovement = default(0.1);
    int minimumSlowSamples = default(2);
    int minimumObservedVehicles = default(3);
    double slowRouteImprovement = default(0.05);
    double minimumRerouteGap @unit(s) = default(30s);
    double densityLambda = default(0.5);
    double trafficDataTtl @unit(s) = default(3s);
    double routeBaseDelay @unit(s) = default(300ms);
    double routeNodeDelay @unit(s) = default(2ms);
    string routingLogPath = default("../../artifacts/logs/routing-events.csv");
}
