package emergencynavigation.scenario;

import org.car2x.veins.nodes.RSU;
import emergencynavigation.apps.FogService;

module ServiceRSU extends RSU
{
    submodules:
        fog: FogService;
}
