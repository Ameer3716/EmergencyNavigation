#pragma once

#include "routing/AStarRouter.h"
#include <omnetpp.h>
#include <memory>

namespace emergencynavigation {
class MistRoutingModule : public omnetpp::cSimpleModule {
public:
    RouteResult compute(const std::string& startEdge, const std::string& destinationEdge,
                        const std::map<std::string, EdgeObservation>& observations, bool dynamic);
    double processingDelay(int expandedNodes) const;
protected:
    void initialize() override;
    void handleMessage(omnetpp::cMessage* message) override { delete message; }
private:
    std::unique_ptr<RoadGraph> graph;
};
}
