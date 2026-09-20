#pragma once

#include "messages/EmergencyNavigation_m.h"
#include "veins/modules/application/ieee80211p/DemoBaseApplLayer.h"

#include <map>
#include <string>

namespace emergencynavigation {

class EmergencyRelayApp : public veins::DemoBaseApplLayer {
public:
    ~EmergencyRelayApp() override;

protected:
    void initialize(int stage) override;
    void onWSM(veins::BaseFrame1609_4* frame) override;
    void handleSelfMsg(omnetpp::cMessage* message) override;
    void finish() override;
    virtual const char* nodeRole() const = 0;
    virtual void onEmergencyAccepted(const EmergencyMessage& message) {}
    virtual void onTrafficBeacon(const TrafficBeacon& message) {}
    virtual void onTrafficStatus(const TrafficStatus& message) {}
    virtual void onRouteRequest(const RouteRequest& message) {}
    virtual void onRouteReply(const RouteReply& message) {}
    virtual void onTLPreemptionRequest(const TLPreemptionRequest& message) {}
    std::string nodeId() const;
    void rememberMessage(const std::string& messageId);
    void logEmergency(const char* action, const EmergencyMessage& message, const std::string& receiverId,
                      bool duplicateDiscarded = false, bool ttlExpired = false) const;
    void logEvent(const char* action, const std::string& eventId, const std::string& messageId) const;
    int hopLimit() const { return maxHops; }
    void sendControl(veins::BaseFrame1609_4* frame);

private:
    void pruneCache();
    std::map<std::string, omnetpp::simtime_t> seen;
    omnetpp::cMessage* cleanupTimer = nullptr;
    int maxHops = 10;
    bool relayEnabled = true;
    omnetpp::simtime_t cacheRetention;
    omnetpp::simtime_t rebroadcastMin;
    omnetpp::simtime_t rebroadcastMax;
    std::string eventLogPath;
    long controlTransmissions = 0, controlBytes = 0, emergencyTransmissions = 0, emergencyBytes = 0;
};

} // namespace emergencynavigation
