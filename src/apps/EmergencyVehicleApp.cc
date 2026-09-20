#include "apps/EmergencyRelayApp.h"

namespace emergencynavigation {

class EmergencyVehicleApp : public EmergencyRelayApp {
protected:
    void initialize(int stage) override {
        EmergencyRelayApp::initialize(stage);
        if (stage == 1) {
            EV_INFO << "ENTITY role=emergency vehicle=" << mobility->getExternalId() << " time=" << simTime() << "\n";
        }
    }
    const char* nodeRole() const override { return "emergency"; }
    void onEmergencyAccepted(const EmergencyMessage& message) override {
        recordScalar("emReceived", 1);
        recordScalar("emEndToEndDelay", simTime().dbl() - message.getGenerationTimestamp());
        logEmergency("ev_processed", message, nodeId());
    }
};

} // namespace emergencynavigation

Define_Module(emergencynavigation::EmergencyVehicleApp);
