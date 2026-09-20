#include "apps/TrafficLightController.h"
#include "veins/modules/mobility/traci/TraCIScenarioManager.h"
#include "veins/modules/mobility/traci/TraCICommandInterface.h"

#include <filesystem>
#include <fstream>

namespace emergencynavigation {

void TrafficLightController::initialize()
{
    recordScalar("initialized", 1);
    lightId = getParentModule()->par("externalId").stdstringValue();
    phaseTimer = new omnetpp::cMessage("preemption phase timer");
}

bool TrafficLightController::request(const std::string& vehicle, const std::string& incoming, double receivedTime)
{
    if (stage != 0) return false;
    auto* command = veins::TraCIScenarioManagerAccess().get()->getCommandInterface();
    auto light = command->trafficlight(lightId);
    const auto links = light.getControlledLinks();
    const auto state = light.getCurrentState();
    greenState.assign(state.size(), 'r');
    size_t index = 0;
    bool found = false;
    for (const auto& group : links) {
        for (const auto& link : group) {
            if (link.incoming.rfind(incoming + "_", 0) == 0 && index < greenState.size()) {
                greenState[index] = 'G';
                found = true;
            }
        }
        ++index;
    }
    if (!found) return false;
    evId = vehicle;
    incomingEdge = incoming;
    requestTime = receivedTime;
    originalProgram = light.getCurrentProgramID();
    originalPhase = light.getCurrentPhaseIndex();
    originalState = state;
    stage = 1;
    log("request_received");
    scheduleAt(simTime() + par("controlProcessingDelay"), phaseTimer);
    return true;
}

void TrafficLightController::handleMessage(omnetpp::cMessage* message)
{
    if (message != phaseTimer) { delete message; return; }
    auto* command = veins::TraCIScenarioManagerAccess().get()->getCommandInterface();
    auto light = command->trafficlight(lightId);
    if (stage == 1) {
        std::string yellow = light.getCurrentState();
        for (char& lamp : yellow) if (lamp == 'G' || lamp == 'g') lamp = 'y';
        light.setState(yellow);
        log("yellow");
        stage = 2;
        scheduleAt(simTime() + par("yellowDuration"), phaseTimer);
    } else if (stage == 2) {
        light.setState(std::string(greenState.size(), 'r'));
        log("all_red");
        stage = 3;
        scheduleAt(simTime() + par("allRedDuration"), phaseTimer);
    } else if (stage == 3) {
        light.setState(greenState);
        log("green_active");
        stage = 4;
        scheduleAt(simTime() + par("maximumHold"), phaseTimer);
    } else if (stage == 4) {
        light.setProgram(originalProgram);
        log("program_restored");
        stage = 0;
    }
}

void TrafficLightController::log(const char* action) const
{
    const std::string path = par("trafficLightLogPath").stdstringValue();
    const bool first = !std::filesystem::exists(path);
    std::ofstream out(path, std::ios::app);
    if (!out) throw omnetpp::cRuntimeError("Cannot open traffic-light log");
    if (first) out << "action,trafficLightId,evId,incomingEdge,requestTime,eventTime,originalProgram,originalPhase,originalState,actualState\n";
    auto* command = veins::TraCIScenarioManagerAccess().get()->getCommandInterface();
    auto light = command->trafficlight(lightId);
    out << action << ',' << lightId << ',' << evId << ',' << incomingEdge << ',' << requestTime << ','
        << simTime().dbl() << ',' << originalProgram << ',' << originalPhase << ',' << originalState << ',' << light.getCurrentState() << '\n';
}
}
Define_Module(emergencynavigation::TrafficLightController);
