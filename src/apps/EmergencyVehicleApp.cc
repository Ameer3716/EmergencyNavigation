#include "apps/EmergencyRelayApp.h"
#include "routing/AStarRouter.h"
#include "metrics/MetricsCollector.h"
#include "apps/MistRoutingModule.h"
#include "veins/modules/mobility/traci/TraCIScenarioManager.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <list>
#include <map>
#include <memory>
#include <sstream>
#include <set>

namespace emergencynavigation {

class EmergencyVehicleApp : public EmergencyRelayApp {
public:
    ~EmergencyVehicleApp() override { cancelAndDelete(routeReady); cancelAndDelete(dynamicTimer); cancelAndDelete(watchdog); cancelAndDelete(preemptionTimer); }
protected:
    void initialize(int stage) override {
        EmergencyRelayApp::initialize(stage);
        if (stage == 0) {
            routeReady = new omnetpp::cMessage("route ready");
            dynamicTimer = new omnetpp::cMessage("dynamic update");
            watchdog = new omnetpp::cMessage("mist watchdog");
            preemptionTimer = new omnetpp::cMessage("preemption check");
        }
        if (stage == 1) {
            EV_INFO << "ENTITY role=emergency vehicle=" << mobility->getExternalId() << " time=" << simTime() << "\n";
            graph = std::make_unique<RoadGraph>(par("roadNetworkFile").stdstringValue());
            recordScalar("roadGraphEdges", static_cast<double>(graph->edgeCount()));
        }
    }
    const char* nodeRole() const override { return "emergency"; }
    void onTrafficBeacon(const TrafficBeacon& message) override {
        beacons[message.getVehicleId()] = {message.getCurrentEdge(), message.getSpeed(), simTime().dbl()};
    }
    void onTrafficStatus(const TrafficStatus& message) override {
        const std::string id = message.getEdgeId();
        if (!status.count(id) || status[id].timestamp <= message.getTimestamp())
            status[id] = {message.getVehicleCount(), message.getMeanSpeed(), message.getTimestamp()};
    }
    void onEmergencyAccepted(const EmergencyMessage& message) override {
        if (navigationStarted) return;
        navigationStarted = true;
        recordScalar("emReceived", 1);
        recordScalar("emEndToEndDelay", simTime().dbl() - message.getGenerationTimestamp());
        auto* metrics = dynamic_cast<MetricsCollector*>(getSimulation()->getSystemModule()->getSubmodule("metrics"));
        if (metrics) metrics->emergencyReceived(message.getGenerationTimestamp(), simTime().dbl());
        logEmergency("ev_processed", message, nodeId());
        decisionStart = simTime().dbl();
        if (par("routingMode").stdstringValue() == "fog_cloud") {
            sendFogRequest(true, "baseline");
            return;
        }
        if (par("routingMode").stdstringValue() == "mist_fallback") {
            if (par("forceMistFailure").boolValue()) {
                logFallback("forced_failure");
                sendFogRequest(false, "forced_failure");
                return;
            }
            scheduleAt(simTime() + par("watchdogThreshold"), watchdog);
        }
        pending = calculateRoute();
        if (pending.edges.empty()) {
            if (par("routingMode").stdstringValue() == "mist_fallback") {
                cancelEvent(watchdog);
                logFallback("invalid_route");
                sendFogRequest(false, "invalid_route");
                return;
            }
            throw omnetpp::cRuntimeError("Mist A* found no route");
        }
        const double delay = mist()->processingDelay(pending.expandedNodes);
        logRoute("computed", "initial", pending, delay);
        scheduleAt(simTime() + delay, routeReady);
    }
    void onRouteReply(const RouteReply& reply) override {
        if (reply.getRequestId() != requestId || reply.getEmergencyVehicleId() != nodeId()) return;
        if (!reply.getRouteValid()) throw omnetpp::cRuntimeError("Fog/cloud returned invalid route");
        RouteResult route;
        std::istringstream ids(reply.getRouteEdges());
        std::string id;
        while (std::getline(ids, id, '|')) route.edges.push_back(id);
        route.cost = reply.getEstimatedCost();
        route.expandedNodes = reply.getExpandedNodes();
        pending = route;
        applyRoute(pending, reply.getComputationLocation());
        recordScalar("routeDecisionLatency", simTime().dbl() - decisionStart);
        recordScalar("fogProcessingDelay", reply.getProcessingDelay());
        recordScalar("cloudBackhaulDelay", reply.getBackhaulDelay());
        recordScalar("routeCommunicationDelay", simTime().dbl() - decisionStart - reply.getProcessingDelay() - reply.getBackhaulDelay());
        if (par("dynamicRouting").boolValue() && !dynamicTimer->isScheduled())
            scheduleAt(simTime() + par("dynamicUpdateInterval"), dynamicTimer);
    }
    void handleSelfMsg(omnetpp::cMessage* message) override {
        if (message == watchdog) {
            cancelEvent(routeReady);
            logFallback("watchdog_timeout");
            sendFogRequest(false, "watchdog_timeout");
            return;
        }
        if (message == preemptionTimer) {
            requestNextLight();
            scheduleAt(simTime() + par("preemptionCheckInterval"), preemptionTimer);
            return;
        }
        if (message == routeReady) {
            if (watchdog->isScheduled()) cancelEvent(watchdog);
            applyRoute(pending, "initial");
            recordScalar("routeDecisionLatency", simTime().dbl() - decisionStart);
            if (par("dynamicRouting").boolValue())
                scheduleAt(simTime() + par("dynamicUpdateInterval"), dynamicTimer);
            return;
        }
        if (message == dynamicTimer) {
            evaluateDynamic();
            scheduleAt(simTime() + par("dynamicUpdateInterval"), dynamicTimer);
            return;
        }
        EmergencyRelayApp::handleSelfMsg(message);
    }
private:
    struct BeaconSample { std::string edge; double speed; double timestamp; };
    std::map<std::string, BeaconSample> beacons;
    std::map<std::string, EdgeObservation> status;
    std::unique_ptr<RoadGraph> graph;
    omnetpp::cMessage* routeReady = nullptr;
    omnetpp::cMessage* dynamicTimer = nullptr;
    omnetpp::cMessage* watchdog = nullptr;
    omnetpp::cMessage* preemptionTimer = nullptr;
    RouteResult pending;
    std::vector<std::string> selected;
    double decisionStart = 0;
    bool navigationStarted = false;
    std::string requestId;
    std::set<std::string> requestedLights;
    std::map<std::string, int> consecutiveSlowSamples;
    double lastRerouteTime = -1e9;

    MistRoutingModule* mist() const {
        auto* module = dynamic_cast<MistRoutingModule*>(getParentModule()->getSubmodule("mist"));
        if (!module) throw omnetpp::cRuntimeError("Emergency vehicle has no mist module");
        return module;
    }

    void requestNextLight() {
        const std::string edgeId = mobility->getRoadId();
        if (edgeId.empty() || edgeId[0] == ':') return;
        const auto& edge = graph->edge(edgeId);
        const std::string lightId = edge.to;
        if (requestedLights.count(lightId)) return;
        auto* command = veins::TraCIScenarioManagerAccess().get()->getCommandInterface();
        auto vehicle = command->vehicle(nodeId());
        const double remaining = std::max(0.0, edge.length - vehicle.getLanePosition());
        const double speed = vehicle.getSpeed();
        const double eta = remaining / std::max(speed, 1.0);
        if (remaining > par("preemptionDistance").doubleValue() && eta > par("preemptionEta").doubleValue()) return;
        auto* request = new TLPreemptionRequest("TLPreemptionRequest");
        populateWSM(request);
        const auto pos = mobility->getPositionAt(simTime());
        request->setEmergencyVehicleId(nodeId().c_str());
        request->setTrafficLightId(lightId.c_str());
        request->setIncomingEdge(edgeId.c_str());
        request->setPositionX(pos.x);
        request->setPositionY(pos.y);
        request->setSpeed(speed);
        request->setEta(eta);
        request->setTimestamp(simTime().dbl());
        request->setByteLength(96);
        sendControl(request);
        requestedLights.insert(lightId);
    }

    void logFallback(const char* reason) const {
        const std::string path = par("fallbackLogPath").stdstringValue();
        const bool first = !std::filesystem::exists(path);
        std::ofstream out(path, std::ios::app);
        if (first) out << "time,mistStart,watchdogThreshold,fallbackReason,fogRequestTime\n";
        out << simTime().dbl() << ',' << decisionStart << ',' << par("watchdogThreshold").doubleValue()
            << ',' << reason << ',' << simTime().dbl() << '\n';
    }
    void sendFogRequest(bool useCloud, const char*) {
        auto* request = new RouteRequest("RouteRequest");
        populateWSM(request);
        requestId = std::string("route-") + nodeId() + "-" + std::to_string(decisionStart);
        request->setRequestId(requestId.c_str());
        request->setTargetRsu(par("nearestFogRsu").stringValue());
        request->setUseCloud(useCloud);
        request->setEmergencyVehicleId(nodeId().c_str());
        request->setStartEdge(mobility->getRoadId().c_str());
        request->setDestinationEdge(par("destinationEdge").stringValue());
        const auto pos = mobility->getPositionAt(simTime());
        request->setStartX(pos.x);
        request->setStartY(pos.y);
        request->setAccidentX(870);
        request->setAccidentY(900);
        request->setRequestTimestamp(simTime().dbl());
        std::ostringstream traffic;
        if (!useCloud) for (const auto& [id, sample] : trafficSnapshot())
            traffic << id << '|' << sample.vehicleCount << '|' << sample.meanSpeed << ';';
        request->setEdgeCosts(traffic.str().c_str());
        request->setByteLength(128 + traffic.str().size());
        sendControl(request);
    }

    std::map<std::string, EdgeObservation> trafficSnapshot() {
        std::map<std::string, EdgeObservation> snapshot;
        const double stale = par("trafficDataTtl").doubleValue();
        for (auto it = beacons.begin(); it != beacons.end();) {
            if (simTime().dbl() - it->second.timestamp > stale) {
                it = beacons.erase(it);
                continue;
            }
            auto& sample = snapshot[it->second.edge];
            sample.meanSpeed += it->second.speed;
            ++sample.vehicleCount;
            sample.timestamp = simTime().dbl();
            ++it;
        }
        for (auto& [edge, sample] : snapshot) sample.meanSpeed /= sample.vehicleCount;
        for (const auto& [edge, sample] : status)
            if (simTime().dbl() - sample.timestamp <= stale) snapshot[edge] = sample;
        return snapshot;
    }
    RouteResult calculateRoute() {
        const auto start = mobility->getRoadId();
        const auto destination = par("destinationEdge").stdstringValue();
        const auto snapshot = trafficSnapshot();
        return mist()->compute(start, destination, snapshot, par("dynamicRouting").boolValue());
    }
    void applyRoute(const RouteResult& route, const char* reason) {
        if (!graph->connected(route.edges) || route.edges.front() != mobility->getRoadId())
            throw omnetpp::cRuntimeError("Ambulance route is disconnected or stale");
        const std::list<std::string> edges(route.edges.begin(), route.edges.end());
        auto* command = veins::TraCIScenarioManagerAccess().get()->getCommandInterface();
        if (!command->vehicle(nodeId()).changeVehicleRoute(edges))
            throw omnetpp::cRuntimeError("SUMO rejected ambulance route");
        selected = route.edges;
        if (!preemptionTimer->isScheduled()) scheduleAt(simTime() + par("preemptionCheckInterval"), preemptionTimer);
        logRoute("applied", reason, route, 0);
        recordScalar("lastRouteCost", route.cost);
    }
    void evaluateDynamic() {
        if (selected.empty()) return;
        auto found = std::find(selected.begin(), selected.end(), mobility->getRoadId());
        if (found == selected.end()) return;
        const std::vector<std::string> remaining(found, selected.end());
        const auto snapshot = trafficSnapshot();
        DynamicAStarRouter router(*graph, snapshot, par("densityLambda"));
        const std::vector<std::string> future(remaining.size() > 1 ? remaining.begin() + 1 : remaining.end(), remaining.end());
        const double oldCost = future.empty() ? 0 : router.routeCost(future);
        pending = mist()->compute(mobility->getRoadId(), par("destinationEdge").stdstringValue(), snapshot, true);
        logRoute("evaluated", "periodic", pending, 0);
        if (pending.edges.empty()) return;
        bool slow = false;
        for (const auto& id : future) {
            auto sample = snapshot.find(id);
            const bool below = sample != snapshot.end() && sample->second.vehicleCount > 0
                && sample->second.meanSpeed < par("congestionSpeedThreshold").doubleValue() * graph->edge(id).speedLimit;
            consecutiveSlowSamples[id] = below ? consecutiveSlowSamples[id] + 1 : 0;
            if (consecutiveSlowSamples[id] >= par("minimumSlowSamples").intValue()) slow = true;
        }
        const double improvement = oldCost > 0 ? (oldCost - pending.cost) / oldCost : 0;
        const bool enoughTime = simTime().dbl() - lastRerouteTime >= par("minimumRerouteGap").doubleValue();
        if (pending.edges != remaining && enoughTime
            && (improvement >= par("minimumRouteImprovement").doubleValue()
                || (slow && improvement >= par("slowRouteImprovement").doubleValue()))) {
            applyRoute(pending, slow ? "low_speed" : "cost_improvement");
            lastRerouteTime = simTime().dbl();
            recordScalar("reroutes", 1);
        }
    }
    static std::string join(const std::vector<std::string>& edges) {
        std::ostringstream out;
        for (size_t i = 0; i < edges.size(); ++i) { if (i) out << '|'; out << edges[i]; }
        return out.str();
    }
    void logRoute(const char* action, const char* reason, const RouteResult& route, double delay) const {
        const std::string path = par("routingLogPath").stdstringValue();
        const bool first = !std::filesystem::exists(path);
        std::ofstream out(path, std::ios::app);
        if (!out) throw omnetpp::cRuntimeError("Cannot open routing log: %s", path.c_str());
        if (first) out << "action,configuration,algorithm,location,time,decisionStart,computationDelay,expandedNodes,estimatedCost,reason,currentEdge,selectedEdges,candidateEdges\n";
        const std::string mode = par("routingMode").stdstringValue();
        const char* configuration = mode == "fog_cloud" ? "FogCloudAStar" :
                                    mode == "mist_fallback" ? "MistDynamicFogFallback" :
                                    mode == "mist_dynamic" ? "MistDynamicAStar" : "MistAStar";
        const char* location = std::string(reason) == "cloud" ? "cloud" :
                               std::string(reason) == "fog" ? "fog" : "mist";
        out << action << ',' << configuration
            << ',' << (par("dynamicRouting").boolValue() ? "dynamic_astar" : "astar")
            << ',' << location << ',' << simTime().dbl() << ',' << decisionStart << ',' << delay
            << ',' << route.expandedNodes << ',' << route.cost << ',' << reason << ',' << mobility->getRoadId()
            << ',' << join(selected) << ',' << join(route.edges) << '\n';
    }
};

} // namespace emergencynavigation

Define_Module(emergencynavigation::EmergencyVehicleApp);
