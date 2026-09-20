package emergencynavigation.apps;

import org.car2x.veins.modules.application.ieee80211p.DemoBaseApplLayer;

simple EmergencyRelayApp extends DemoBaseApplLayer
{
    parameters:
        int maxHops = default(10);
        bool relayEnabled = default(true);
        double cacheRetention @unit(s) = default(60s);
        double rebroadcastMin @unit(s) = default(5ms);
        double rebroadcastMax @unit(s) = default(20ms);
        string eventLogPath = default("../../artifacts/logs/emergency-events.csv");
}
