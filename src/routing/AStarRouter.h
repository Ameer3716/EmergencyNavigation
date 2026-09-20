#pragma once

#include "routing/RoadGraph.h"

#include <map>
#include <string>
#include <vector>

namespace emergencynavigation {

struct EdgeObservation { int vehicleCount = 0; double meanSpeed = 0; double timestamp = 0; };
struct RouteResult { std::vector<std::string> edges; double cost = 0; int expandedNodes = 0; };

class AStarRouter {
public:
    explicit AStarRouter(const RoadGraph& graph) : graph(graph) {}
    RouteResult route(const std::string& startEdge, const std::string& destinationEdge) const;
    double routeCost(const std::vector<std::string>& edges) const;
protected:
    virtual double edgeCost(const RoadEdge& edge) const;
    const RoadGraph& graph;
};

class DynamicAStarRouter : public AStarRouter {
public:
    DynamicAStarRouter(const RoadGraph& graph, const std::map<std::string, EdgeObservation>& observations,
                       double lambda, double capacityPerMeter = 1.0 / 7.5);
protected:
    double edgeCost(const RoadEdge& edge) const override;
private:
    const std::map<std::string, EdgeObservation>& observations;
    double lambda;
    double capacityPerMeter;
};

} // namespace emergencynavigation
