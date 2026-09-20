#pragma once

#include <omnetpp.h>
#include <string>

namespace emergencynavigation {
class TrafficLightController : public omnetpp::cSimpleModule {
public:
    ~TrafficLightController() override { cancelAndDelete(phaseTimer); }
    bool request(const std::string& evId, const std::string& incomingEdge, double requestTime);
protected:
    void initialize() override;
    void handleMessage(omnetpp::cMessage* message) override;
private:
    void log(const char* action) const;
    std::string lightId, originalProgram, originalState, evId, incomingEdge, greenState;
    double requestTime = 0;
    int originalPhase = -1;
    int stage = 0;
    omnetpp::cMessage* phaseTimer = nullptr;
};
}
