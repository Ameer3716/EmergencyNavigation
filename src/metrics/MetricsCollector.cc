#include "metrics/MetricsCollector.h"
#include "veins/modules/mobility/traci/TraCIScenarioManager.h"
#include "veins/modules/mobility/traci/TraCICommandInterface.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <tuple>
#include <iomanip>

namespace emergencynavigation {

void MetricsCollector::initialize()
{
    recordScalar("initialized", 1);
    pollTimer = new omnetpp::cMessage("mobility metric poll");
    const std::string path = par("mobilityLogPath").stdstringValue();
    const bool first = !std::filesystem::exists(path) || std::filesystem::file_size(path) == 0;
    trace.open(path, std::ios::app);
    trace << std::setprecision(15);
    if (!trace) throw omnetpp::cRuntimeError("Cannot open mobility log");
    if (first) trace << "time,vehicleId,edge,lanePosition,speed,distance,stopDuration,event,trafficLightWaiting,activeBackgroundVehicles,nextTls,tlsDistance,linkState,phaseIndex,signalState,junctionEvent,crossingTls,crossingPhase,crossingState,crossingLinkState,wholeRouteBelow1,fullStops\n";
    scheduleAt(simTime() + par("pollInterval"), pollTimer);
}

void MetricsCollector::navigationReleased()
{
    if (released < 0) { released = simTime().dbl(); recordScalar("evNavigationReleaseTime", released); }
}

void MetricsCollector::emergencyReceived(double eventGeneration, double eventReception)
{
    if (generation >= 0) return;
    generation = eventGeneration;
    reception = eventReception;
    recordScalar("emGenerationTime", generation);
    recordScalar("emReceptionTime", reception);
    recordScalar("emEndToEndDelay", reception - generation);
}

void MetricsCollector::handleMessage(omnetpp::cMessage* message)
{
    if (message != pollTimer) { delete message; return; }
    auto* manager = veins::TraCIScenarioManagerAccess().get();
    auto* command = manager ? manager->getCommandInterface() : nullptr;
    if (command) {
        const std::string id = par("emergencyVehicleId").stdstringValue();
        // SUMO supplies a new state once per manager step. Poll at 100 ms, but reuse
        // that state between steps rather than sending identical TraCI queries.
        const long sumoStep = std::floor((simTime().dbl() + 1e-9) / manager->par("updateInterval").doubleValue());
        if (sumoStep != lastSumoStep) {
            junctionEvent.clear();
            crossingLight.clear();
            crossingState.clear();
            crossingPhase = -1;
            crossingLinkState = '?';
            lastSumoStep = sumoStep;
            const auto ids = command->getVehicleIds();
            activeBackground = 0;
            for (const auto& vehicleId : ids) if (vehicleId != id && vehicleId != "accident") {
                backgroundSeen.insert(vehicleId);
                ++activeBackground;
            }
            peakBackground = std::max(peakBackground, activeBackground);
            present = std::find(ids.begin(), ids.end(), id) != ids.end();
            if (present) {
                auto vehicle = command->vehicle(id);
                lastSpeed = vehicle.getSpeed();
                distance = vehicle.getDistanceTravelled();
                const std::string newEdge = vehicle.getRoadId();
                // Entry is observed on the first SUMO sample leaving an external
                // approach. Record both current phase and last approach link state;
                // the crossing instant is only localized to a 500 ms interval.
                if (released >= 0 && !lastEdge.empty() && lastEdge[0] != ':'
                    && newEdge != lastEdge && !nextLight.empty()) {
                    junctionEvent = "junction_entry";
                    crossingLight = nextLight;
                    auto light = command->trafficlight(crossingLight);
                    crossingPhase = light.getCurrentPhaseIndex();
                    crossingState = light.getCurrentState();
                    crossingLinkState = nextLinkIndex >= 0 && nextLinkIndex < int(crossingState.size())
                        ? crossingState[nextLinkIndex] : '?';
                    ++crossings;
                    if (crossingLinkState == 'G' || crossingLinkState == 'g') ++greenCrossings;
                }
                lastEdge = newEdge;
                lastLanePosition = vehicle.getLanePosition();
                nextLight.clear(); signalState.clear(); nextLightDistance = -1; signalPhase = -1; nextLinkState = '?'; nextLinkIndex = -1;
                const auto lights = vehicle.getNextTls();
                if (!lights.empty()) {
                    nextLight = std::get<0>(lights.front());
                    nextLinkIndex = std::get<1>(lights.front());
                    nextLightDistance = std::get<2>(lights.front());
                    nextLinkState = std::get<3>(lights.front());
                    auto light = command->trafficlight(nextLight);
                    signalState = light.getCurrentState();
                    signalPhase = light.getCurrentPhaseIndex();
                }
                nearLight = false;
                if (lastSpeed < 0.1 && reception >= 0) {
                    nearLight = !lights.empty() && nextLightDistance <= 20.0 && nextLightDistance >= 0;
                }
                if (released >= 0) {
                    if (lastSpeed >= 1) { wasMoving = true; inStop = false; }
                    if (lastSpeed < 0.1 && wasMoving && !inStop) { ++fullStops; inStop = true; }
                }
            }
        }
        if (present) {
            const double speed = lastSpeed;
            if (!seenVehicle && speed > 0.1) { seenVehicle = true; departure = simTime().dbl(); }
            if (speed < 0.1) stopDuration += par("pollInterval").doubleValue();
            if (speed < 0.1 && reception >= 0 && nearLight)
                trafficLightWaiting += par("pollInterval").doubleValue();
            if (released >= 0) {
                if (speed < 1) slowTime += par("pollInterval").doubleValue();
                if (speed < 0.1) wholeRouteStopped += par("pollInterval").doubleValue();
            }
            trace << simTime().dbl() << ',' << id << ',' << lastEdge << ',' << lastLanePosition
                  << ',' << speed << ',' << distance << ',' << stopDuration << ",position,"
                  << trafficLightWaiting << ',' << activeBackground << ',' << nextLight << ',' << nextLightDistance
                  << ',' << nextLinkState << ',' << signalPhase << ',' << signalState << ',' << junctionEvent
                  << ',' << crossingLight << ',' << crossingPhase << ',' << crossingState << ',' << crossingLinkState
                  << ',' << slowTime << ',' << fullStops << '\n';
            junctionEvent.clear();
        } else if (seenVehicle && !finishedVehicle) {
            finishedVehicle = true;
            arrival = simTime().dbl();
            trace << arrival << ',' << id << ",,,," << distance << ',' << stopDuration << ",arrival,"
                  << trafficLightWaiting << ',' << activeBackground << '\n';
            recordScalar("evDepartureTime", departure);
            recordScalar("evArrivalTime", arrival);
            recordScalar("evTravelTime", arrival - departure);
            recordScalar("evDistance", distance);
            recordScalar("evStopDuration", stopDuration);
            recordScalar("evTrafficLightWaitingTime", trafficLightWaiting);
            recordScalar("evTimeBelow1Mps", slowTime);
            recordScalar("evWholeRouteStoppedTime", wholeRouteStopped);
            recordScalar("evFullStops", fullStops);
            recordScalar("evSignalCrossings", crossings);
            recordScalar("evSignalsPassedOnGreen", greenCrossings);
            if (crossings > 0) recordScalar("evGreenCrossingFraction", double(greenCrossings) / crossings);
            if (generation >= 0) recordScalar("evResponseTime", arrival - generation);
            recordScalar("accidentArrivalConfirmed", lastEdge == par("destinationEdge").stdstringValue() && lastLanePosition > par("minimumArrivalPosition").doubleValue());
        }
    }
    if (!finishedVehicle) scheduleAt(simTime() + par("pollInterval"), pollTimer);
}

void MetricsCollector::finish()
{
    if (!finishedVehicle) recordScalar("accidentArrivalConfirmed", 0);
    recordScalar("backgroundVehiclesSeenUntilArrival", backgroundSeen.size());
    recordScalar("peakActiveBackgroundVehicles", peakBackground);
    cancelAndDelete(pollTimer);
    pollTimer = nullptr;
    trace.close();
}
}
Define_Module(emergencynavigation::MetricsCollector);
