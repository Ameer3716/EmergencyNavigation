#include "metrics/MetricsCollector.h"
#include "veins/modules/mobility/traci/TraCIScenarioManager.h"
#include "veins/modules/mobility/traci/TraCICommandInterface.h"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <tuple>

namespace emergencynavigation {

void MetricsCollector::initialize()
{
    recordScalar("initialized", 1);
    pollTimer = new omnetpp::cMessage("mobility metric poll");
    const std::string path = par("mobilityLogPath").stdstringValue();
    const bool first = !std::filesystem::exists(path);
    trace.open(path, std::ios::app);
    if (!trace) throw omnetpp::cRuntimeError("Cannot open mobility log");
    if (first) trace << "time,vehicleId,edge,lanePosition,speed,distance,stopDuration,event\n";
    scheduleAt(simTime() + par("pollInterval"), pollTimer);
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
        const auto ids = command->getVehicleIds();
        const bool present = std::find(ids.begin(), ids.end(), id) != ids.end();
        if (present) {
            auto vehicle = command->vehicle(id);
            const double speed = vehicle.getSpeed();
            if (!seenVehicle && speed > 0.1) { seenVehicle = true; departure = simTime().dbl(); }
            distance = vehicle.getDistanceTravelled();
            lastEdge = vehicle.getRoadId();
            lastLanePosition = vehicle.getLanePosition();
            if (speed < 0.1) stopDuration += par("pollInterval").doubleValue();
            if (speed < 0.1 && reception >= 0) {
                const auto lights = vehicle.getNextTls();
                if (!lights.empty() && std::get<2>(lights.front()) <= 20.0)
                    trafficLightWaiting += par("pollInterval").doubleValue();
            }
            lastSpeed = speed;
            trace << simTime().dbl() << ',' << id << ',' << vehicle.getRoadId() << ',' << vehicle.getLanePosition()
                  << ',' << speed << ',' << distance << ',' << stopDuration << ",position\n";
        } else if (seenVehicle && !finishedVehicle) {
            finishedVehicle = true;
            arrival = simTime().dbl();
            trace << arrival << ',' << id << ",,,," << distance << ',' << stopDuration << ",arrival\n";
            recordScalar("evDepartureTime", departure);
            recordScalar("evArrivalTime", arrival);
            recordScalar("evTravelTime", arrival - departure);
            recordScalar("evDistance", distance);
            recordScalar("evStopDuration", stopDuration);
            recordScalar("evTrafficLightWaitingTime", trafficLightWaiting);
            if (generation >= 0) recordScalar("evResponseTime", arrival - generation);
            recordScalar("accidentArrivalConfirmed", lastEdge == par("destinationEdge").stdstringValue() && lastLanePosition > par("minimumArrivalPosition").doubleValue());
        }
    }
    if (!finishedVehicle) scheduleAt(simTime() + par("pollInterval"), pollTimer);
}

void MetricsCollector::finish()
{
    if (!finishedVehicle) recordScalar("accidentArrivalConfirmed", 0);
    cancelAndDelete(pollTimer);
    pollTimer = nullptr;
    trace.close();
}
}
Define_Module(emergencynavigation::MetricsCollector);
