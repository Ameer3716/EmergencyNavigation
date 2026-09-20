#include "apps/EmergencyRelayApp.h"
#include "apps/FogService.h"
#include "apps/CloudService.h"
#include "apps/TrafficLightController.h"
#include "veins/modules/mobility/traci/TraCIScenarioManager.h"

#include <algorithm>
#include <map>
#include <sstream>

namespace emergencynavigation {

class RsuApp : public EmergencyRelayApp {
public:
    ~RsuApp() override { cancelAndDelete(detectionTimer); cancelAndDelete(statusTimer); }

protected:
    void initialize(int stage) override {
        EmergencyRelayApp::initialize(stage);
        if (stage == 0) {
            detectionTimer = new omnetpp::cMessage("accident detection");
            statusTimer = new omnetpp::cMessage("traffic status timer");
        }
        if (stage == 1) {
            EV_INFO << "ENTITY role=rsu module=" << getParentModule()->getFullPath() << " time=" << simTime() << "\n";
            if (par("accidentDetector").boolValue()) scheduleAt(par("accidentTime"), detectionTimer);
            scheduleAt(simTime() + par("trafficStatusInterval"), statusTimer);
        }
    }
    const char* nodeRole() const override { return "rsu"; }
    void onTrafficBeacon(const TrafficBeacon& beacon) override {
        observations[beacon.getVehicleId()] = {beacon.getCurrentEdge(), beacon.getSpeed(), simTime().dbl()};
    }
    void onRouteRequest(const RouteRequest& request) override {
        if (request.getTargetRsu() != getParentModule()->getFullPath()) return;
        auto* fog = dynamic_cast<FogService*>(getParentModule()->getSubmodule("fog"));
        if (!fog) throw omnetpp::cRuntimeError("Route request reached RSU without fog service");
        const bool cloudNeeded = request.getUseCloud()
            && !fog->withinServiceArea(request.getAccidentX(), request.getAccidentY());
        std::map<std::string, EdgeObservation> snapshot;
        std::istringstream data(request.getEdgeCosts());
        std::string record;
        while (std::getline(data, record, ';')) {
            std::istringstream fields(record);
            std::string id, count, speed;
            if (std::getline(fields, id, '|') && std::getline(fields, count, '|') && std::getline(fields, speed, '|'))
                snapshot[id] = {std::stoi(count), std::stod(speed), simTime().dbl()};
        }
        RouteResult result;
        double processing = 0;
        double backhaul = 0;
        const char* location = "fog";
        if (cloudNeeded) {
            auto* cloud = dynamic_cast<CloudService*>(getSimulation()->getSystemModule()->getSubmodule("cloud"));
            if (!cloud) throw omnetpp::cRuntimeError("Cloud service missing");
            result = cloud->compute(request.getStartEdge(), request.getDestinationEdge());
            processing = cloud->processingDelay(result.expandedNodes);
            backhaul = 2 * cloud->backhaulDelay();
            location = "cloud";
        } else {
            result = fog->compute(request.getStartEdge(), request.getDestinationEdge(), snapshot, !request.getUseCloud());
            processing = fog->processingDelay(result.expandedNodes);
        }
        auto* reply = new RouteReply("RouteReply");
        populateWSM(reply);
        reply->setRequestId(request.getRequestId());
        reply->setEmergencyVehicleId(request.getEmergencyVehicleId());
        std::string edges;
        for (const auto& id : result.edges) { if (!edges.empty()) edges += '|'; edges += id; }
        reply->setRouteEdges(edges.c_str());
        reply->setEstimatedCost(result.cost);
        reply->setComputationLocation(location);
        reply->setComputationStarted(simTime().dbl() + backhaul / 2);
        reply->setComputationFinished(simTime().dbl() + backhaul / 2 + processing);
        reply->setRouteValid(!result.edges.empty());
        reply->setBackhaulDelay(backhaul);
        reply->setProcessingDelay(processing);
        reply->setExpandedNodes(result.expandedNodes);
        reply->setByteLength(128 + edges.size());
        scheduleAt(simTime() + processing + backhaul, reply);
    }
    void onTLPreemptionRequest(const TLPreemptionRequest& request) override {
        auto* system = getSimulation()->getSystemModule();
        for (int i = 0; i < system->getSubmoduleVectorSize("tls"); ++i) {
            auto* light = system->getSubmodule("tls", i);
            if (!light || light->par("externalId").stdstringValue() != request.getTrafficLightId()) continue;
            auto* controller = dynamic_cast<TrafficLightController*>(light->getSubmodule("controller"));
            if (controller) controller->request(request.getEmergencyVehicleId(), request.getIncomingEdge(), request.getTimestamp());
            return;
        }
    }
    void handleSelfMsg(omnetpp::cMessage* message) override {
        if (auto* reply = dynamic_cast<RouteReply*>(message)) {
            sendControl(reply);
            return;
        }
        if (message == statusTimer) {
            std::map<std::string, std::pair<int, double>> byEdge;
            for (auto it = observations.begin(); it != observations.end();) {
                if (simTime().dbl() - it->second.timestamp > par("trafficDataTtl").doubleValue()) {
                    it = observations.erase(it);
                    continue;
                }
                auto& sample = byEdge[it->second.edge];
                ++sample.first;
                sample.second += it->second.speed;
                ++it;
            }
            for (const auto& [edge, sample] : byEdge) {
                auto* status = new TrafficStatus("TrafficStatus");
                populateWSM(status);
                status->setEdgeId(edge.c_str());
                status->setVehicleCount(sample.first);
                status->setMeanSpeed(sample.second / sample.first);
                status->setTimestamp(simTime().dbl());
                status->setByteLength(80);
                sendControl(status);
            }
            scheduleAt(simTime() + par("trafficStatusInterval"), statusTimer);
            return;
        }
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
    struct VehicleObservation { std::string edge; double speed; double timestamp; };
    std::map<std::string, VehicleObservation> observations;
    omnetpp::cMessage* detectionTimer = nullptr;
    omnetpp::cMessage* statusTimer = nullptr;
    double stoppedSince = -1;
    bool occurrenceLogged = false;
};

} // namespace emergencynavigation

Define_Module(emergencynavigation::RsuApp);
