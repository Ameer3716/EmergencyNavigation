package emergencynavigation.apps;

simple TrafficLightController
{
    @class(emergencynavigation::TrafficLightController);
    double controlProcessingDelay @unit(s) = default(150ms);
    double yellowDuration @unit(s) = default(2s);
    double allRedDuration @unit(s) = default(1s);
    double maximumHold @unit(s) = default(25s);
    string trafficLightLogPath = default("../../artifacts/logs/traffic-light-events.csv");
}
