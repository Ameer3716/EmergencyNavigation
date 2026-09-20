package emergencynavigation.scenario;

import org.car2x.veins.nodes.RSU;
import org.car2x.veins.nodes.Scenario;
import org.car2x.veins.nodes.TrafficLight;

network EmergencyGridScenario extends Scenario
{
    submodules:
        rsu[3]: RSU {
        }
        tls[0]: TrafficLight {
        }
}
