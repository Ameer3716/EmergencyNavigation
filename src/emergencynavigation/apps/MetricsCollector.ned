package emergencynavigation.apps;

simple MetricsCollector
{
    @class(emergencynavigation::MetricsCollector);
    string emergencyVehicleId = default("ambulance");
    string destinationEdge = default("D2D3");
    double minimumArrivalPosition @unit(m) = default(250m);
    double pollInterval @unit(s) = default(500ms);
    string mobilityLogPath = default("../../artifacts/logs/mobility-events.csv");
}
