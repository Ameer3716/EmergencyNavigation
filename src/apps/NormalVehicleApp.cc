#include "veins/modules/application/ieee80211p/DemoBaseApplLayer.h"

namespace emergencynavigation {

class NormalVehicleApp : public veins::DemoBaseApplLayer {
protected:
    void initialize(int stage) override {
        veins::DemoBaseApplLayer::initialize(stage);
        if (stage == 1) {
            EV_INFO << "ENTITY role=normal vehicle=" << mobility->getExternalId() << " time=" << simTime() << "\n";
        }
    }
};

} // namespace emergencynavigation

Define_Module(emergencynavigation::NormalVehicleApp);
