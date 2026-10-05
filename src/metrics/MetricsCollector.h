#pragma once

#include <omnetpp.h>
#include <fstream>
#include <set>

namespace emergencynavigation {
class MetricsCollector : public omnetpp::cSimpleModule {
public:
    ~MetricsCollector() override { cancelAndDelete(pollTimer); }
    void emergencyReceived(double generation, double reception);
protected:
    void initialize() override;
    void handleMessage(omnetpp::cMessage* message) override;
    void finish() override;
private:
    omnetpp::cMessage* pollTimer = nullptr;
    bool seenVehicle = false, finishedVehicle = false;
    double departure = -1, arrival = -1, generation = -1, reception = -1;
    double distance = 0, stopDuration = 0, trafficLightWaiting = 0, lastSpeed = 0;
    double lastLanePosition = 0;
    std::string lastEdge;
    std::ofstream trace;
    std::set<std::string> backgroundSeen;
    int peakBackground = 0;
    long lastSumoStep = -1;
    int activeBackground = 0;
    bool present = false, nearLight = false;
};
}
