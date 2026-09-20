#include "apps/EmergencyRelayApp.h"
#include "veins/modules/mobility/traci/TraCIScenarioManager.h"

#include <algorithm>

namespace emergencynavigation {

class RsuApp : public EmergencyRelayApp {
public:
    ~RsuApp() override { cancelAndDelete(detectionTimer); }

protected:
    void initialize(int stage) override {
        EmergencyRelayApp::initialize(stage);
        if (stage == 0) {
            detectionTimer = new omnetpp::cMessage("accident detection");
        }
        if (stage == 1) {
            EV_INFO << "ENTITY role=rsu module=" << getParentModule()->getFullPath() << " time=" << simTime() << "\n";
            if (par("accidentDetector").boolValue()) scheduleAt(par("accidentTime"), detectionTimer);
        }
    }
    const char* nodeRole() const override { return "rsu"; }
    void handleSelfMsg(omnetpp::cMessage* message) override {
        if (message != detectionTimer) {
            EmergencyRelayApp::handleSelfMsg(message);
            return;
        }
        const std::string eventId = "accident-1";
        const std::string messageId = "em-accident-1";
        if (!occurrenceLogged) {
            logEvent("accident_occurrence", eventId, messageId);
            occurrenceLogged = true;
        }
        auto* manager = veins::TraCIScenarioManagerAccess().get();
        auto* command = manager ? manager->getCommandInterface() : nullptr;
        bool stationary = false;
        if (command) {
            const std::string accidentId = par("accidentVehicleId").stdstringValue();
            const auto ids = command->getVehicleIds();
            if (std::find(ids.begin(), ids.end(), accidentId) != ids.end()) {
                auto vehicle = command->vehicle(accidentId);
                stationary = vehicle.getRoadId() == par("accidentRoad").stdstringValue()
                    && vehicle.getLanePosition() <= 50 && vehicle.getSpeed() < 0.1;
            }
        }
        if (stationary) {
            if (stoppedSince < 0) stoppedSince = simTime().dbl();
            if (simTime().dbl() - stoppedSince >= par("stoppedSeconds").doubleValue()) {
                logEvent("accident_detection", eventId, messageId);
                auto* emergency = new EmergencyMessage("EmergencyMessage");
                populateWSM(emergency);
                emergency->setEventId(eventId.c_str());
                emergency->setMessageId(messageId.c_str());
                emergency->setGenerationTimestamp(simTime().dbl());
                emergency->setAccidentX(870);
                emergency->setAccidentY(900);
                emergency->setSenderId(nodeId().c_str());
                emergency->setRemainingHops(hopLimit());
                emergency->setHopCount(0);
                emergency->setPayloadBytes(par("payloadBytes"));
                emergency->setByteLength(par("payloadBytes").intValue() + 10);
                rememberMessage(messageId);
                logEmergency("generated", *emergency, "broadcast");
                scheduleAt(simTime(), emergency);
                return;
            }
        } else {
            stoppedSince = -1;
        }
        scheduleAt(simTime() + 0.5, detectionTimer);
    }

private:
    omnetpp::cMessage* detectionTimer = nullptr;
    double stoppedSince = -1;
    bool occurrenceLogged = false;
};

} // namespace emergencynavigation

Define_Module(emergencynavigation::RsuApp);
