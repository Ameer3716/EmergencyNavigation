#include "veins/modules/application/ieee80211p/DemoBaseApplLayer.h"

namespace emergencynavigation {

class RsuApp : public veins::DemoBaseApplLayer {
protected:
    void initialize(int stage) override {
        veins::DemoBaseApplLayer::initialize(stage);
        if (stage == 1) {
            EV_INFO << "ENTITY role=rsu module=" << getParentModule()->getFullPath() << " time=" << simTime() << "\n";
        }
    }
};

} // namespace emergencynavigation

Define_Module(emergencynavigation::RsuApp);
