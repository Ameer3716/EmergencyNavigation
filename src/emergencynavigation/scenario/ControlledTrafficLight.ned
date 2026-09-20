package emergencynavigation.scenario;

import org.car2x.veins.nodes.TrafficLight;
import emergencynavigation.apps.TrafficLightController;

module ControlledTrafficLight extends TrafficLight
{
    submodules:
        controller: TrafficLightController;
}
