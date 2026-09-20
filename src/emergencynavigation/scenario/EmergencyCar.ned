package emergencynavigation.scenario;

import org.car2x.veins.nodes.Car;
import emergencynavigation.apps.MistRoutingModule;

module EmergencyCar extends Car
{
    parameters:
        applType = "emergencynavigation.apps.EmergencyVehicleApp";
    submodules:
        mist: MistRoutingModule;
}
