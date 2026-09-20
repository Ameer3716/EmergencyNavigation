#include "apps/EmergencyRelayApp.h"

namespace emergencynavigation {

class NormalVehicleApp : public EmergencyRelayApp {
protected:
    void initialize(int stage) override {
        EmergencyRelayApp::initialize(stage);
        if (stage == 1) {
            EV_INFO << "ENTITY role=normal vehicle=" << mobility->getExternalId() << " time=" << simTime() << "\n";
        }
    }
    const char* nodeRole() const override { return "normal"; }
};

} // namespace emergencynavigation

Define_Module(emergencynavigation::NormalVehicleApp);
