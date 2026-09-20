package emergencynavigation.scenario;

import org.car2x.veins.nodes.Scenario;
import org.car2x.veins.nodes.TrafficLight;
import emergencynavigation.scenario.ServiceRSU;
import emergencynavigation.apps.CloudService;
import emergencynavigation.apps.MetricsCollector;

network EmergencyGridScenario extends Scenario
{
    submodules:
        rsu[3]: ServiceRSU {
        }
        tls[0]: TrafficLight {
        }
        cloud: CloudService {
        }
        metrics: MetricsCollector {
        }
}
