#include "apps/EmergencyRelayApp.h"

namespace emergencynavigation {

class NormalVehicleApp : public EmergencyRelayApp {
public:
    ~NormalVehicleApp() override { cancelAndDelete(beaconTimer); }
protected:
    void initialize(int stage) override {
        EmergencyRelayApp::initialize(stage);
        if (stage == 1) {
            EV_INFO << "ENTITY role=normal vehicle=" << mobility->getExternalId() << " time=" << simTime() << "\n";
            beaconTimer = new omnetpp::cMessage("traffic beacon timer");
            scheduleAt(simTime() + uniform(0, par("trafficBeaconInterval").doubleValue()), beaconTimer);
        }
    }
    const char* nodeRole() const override { return "normal"; }
    void handleSelfMsg(omnetpp::cMessage* message) override {
        if (message != beaconTimer) return EmergencyRelayApp::handleSelfMsg(message);
        auto* beacon = new TrafficBeacon("TrafficBeacon");
        populateWSM(beacon);
        const auto pos = mobility->getPositionAt(simTime());
        beacon->setVehicleId(nodeId().c_str());
        beacon->setPositionX(pos.x);
        beacon->setPositionY(pos.y);
        beacon->setSpeed(mobility->getSpeed());
        beacon->setCurrentEdge(mobility->getRoadId().c_str());
        beacon->setTimestamp(simTime().dbl());
        beacon->setByteLength(80);
        sendControl(beacon);
        scheduleAt(simTime() + par("trafficBeaconInterval"), beaconTimer);
    }
private:
    omnetpp::cMessage* beaconTimer = nullptr;
};

} // namespace emergencynavigation

Define_Module(emergencynavigation::NormalVehicleApp);
