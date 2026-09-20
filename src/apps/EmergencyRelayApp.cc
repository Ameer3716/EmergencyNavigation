#include "apps/EmergencyRelayApp.h"

#include <filesystem>
#include <fstream>

namespace emergencynavigation {

EmergencyRelayApp::~EmergencyRelayApp()
{
    cancelAndDelete(cleanupTimer);
}

void EmergencyRelayApp::initialize(int stage)
{
    veins::DemoBaseApplLayer::initialize(stage);
    if (stage == 0) {
        maxHops = par("maxHops");
        relayEnabled = par("relayEnabled").boolValue();
        cacheRetention = par("cacheRetention");
        rebroadcastMin = par("rebroadcastMin");
        rebroadcastMax = par("rebroadcastMax");
        eventLogPath = par("eventLogPath").stdstringValue();
        if (maxHops < 1 || rebroadcastMin < 0 || rebroadcastMax < rebroadcastMin) {
            throw omnetpp::cRuntimeError("Invalid emergency relay parameters");
        }
        cleanupTimer = new omnetpp::cMessage("emergency cache cleanup");
        scheduleAt(simTime() + 10, cleanupTimer);
    }
}

std::string EmergencyRelayApp::nodeId() const
{
    return mobility ? mobility->getExternalId() : getParentModule()->getFullPath();
}

void EmergencyRelayApp::pruneCache()
{
    for (auto it = seen.begin(); it != seen.end();) {
        if (simTime() - it->second > cacheRetention) it = seen.erase(it);
        else ++it;
    }
}

void EmergencyRelayApp::rememberMessage(const std::string& messageId)
{
    pruneCache();
    seen[messageId] = simTime();
}

void EmergencyRelayApp::logEmergency(const char* action, const EmergencyMessage& message,
                                     const std::string& receiverId, bool duplicateDiscarded,
                                     bool ttlExpired) const
{
    const bool newFile = !std::filesystem::exists(eventLogPath);
    std::ofstream out(eventLogPath, std::ios::app);
    if (!out) throw omnetpp::cRuntimeError("Cannot open emergency event log: %s", eventLogPath.c_str());
    if (newFile) {
        out << "action,eventId,messageId,senderId,receiverId,nodeRole,generationTime,eventTime,remainingHops,hopCount,packetBytes,duplicateDiscarded,ttlExpired\n";
    }
    out << action << ',' << message.getEventId() << ',' << message.getMessageId() << ','
        << message.getSenderId() << ',' << receiverId << ',' << nodeRole() << ','
        << message.getGenerationTimestamp() << ',' << simTime().dbl() << ','
        << message.getRemainingHops() << ',' << message.getHopCount() << ','
        << message.getByteLength() << ',' << duplicateDiscarded << ',' << ttlExpired << '\n';
}

void EmergencyRelayApp::logEvent(const char* action, const std::string& eventId,
                                 const std::string& messageId) const
{
    const bool newFile = !std::filesystem::exists(eventLogPath);
    std::ofstream out(eventLogPath, std::ios::app);
    if (!out) throw omnetpp::cRuntimeError("Cannot open emergency event log: %s", eventLogPath.c_str());
    if (newFile) {
        out << "action,eventId,messageId,senderId,receiverId,nodeRole,generationTime,eventTime,remainingHops,hopCount,packetBytes,duplicateDiscarded,ttlExpired\n";
    }
    out << action << ',' << eventId << ',' << messageId << ',' << nodeId() << ",," << nodeRole()
        << ",," << simTime().dbl() << ",,,,,\n";
}

void EmergencyRelayApp::onWSM(veins::BaseFrame1609_4* frame)
{
    auto* message = dynamic_cast<EmergencyMessage*>(frame);
    if (!message) return;
    pruneCache();
    const std::string id = message->getMessageId();
    if (seen.count(id)) {
        logEmergency("duplicate_discard", *message, nodeId(), true);
        return;
    }
    rememberMessage(id);
    logEmergency("receive", *message, nodeId());
    onEmergencyAccepted(*message);
    if (std::string(nodeRole()) == "emergency") return;
    if (!relayEnabled) return;
    if (message->getRemainingHops() <= 1) {
        logEmergency("ttl_expired", *message, nodeId(), false, true);
        return;
    }
    auto* forward = message->dup();
    forward->setRemainingHops(message->getRemainingHops() - 1);
    forward->setHopCount(message->getHopCount() + 1);
    forward->setSenderId(nodeId().c_str());
    scheduleAt(simTime() + uniform(rebroadcastMin.dbl(), rebroadcastMax.dbl()), forward);
}

void EmergencyRelayApp::handleSelfMsg(omnetpp::cMessage* message)
{
    if (message == cleanupTimer) {
        pruneCache();
        scheduleAt(simTime() + 10, cleanupTimer);
        return;
    }
    if (auto* emergency = dynamic_cast<EmergencyMessage*>(message)) {
        logEmergency("transmit", *emergency, "broadcast");
        sendDown(emergency);
        return;
    }
    veins::DemoBaseApplLayer::handleSelfMsg(message);
}

} // namespace emergencynavigation
