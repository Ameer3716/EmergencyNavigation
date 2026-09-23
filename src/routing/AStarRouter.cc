#include "routing/AStarRouter.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
#include <stdexcept>

namespace emergencynavigation {

double AStarRouter::edgeCost(const RoadEdge& edge) const { return edge.length / edge.speedLimit; }

double AStarRouter::routeCost(const std::vector<std::string>& edges) const
{
    if (!graph.connected(edges)) throw std::invalid_argument("Route is disconnected");
    double cost = 0;
    for (const auto& id : edges) cost += edgeCost(graph.edge(id));
    return cost;
}

RouteResult AStarRouter::route(const std::string& startEdge, const std::string& destinationEdge) const
{
    graph.edge(startEdge);
    const auto& target = graph.edge(destinationEdge);
    if (startEdge == destinationEdge) return {{startEdge}, 0, 0};
    const auto goal = graph.junction(target.from);
    auto heuristic = [&](const std::string& id) {
        if (id == destinationEdge) return 0.0;
        const auto p = graph.junction(graph.edge(id).to);
        return std::hypot(goal.x - p.x, goal.y - p.y) / graph.maximumSpeed();
    };
    using Entry = std::pair<double, std::string>;
    std::priority_queue<Entry, std::vector<Entry>, std::greater<Entry>> frontier;
    std::map<std::string, double> distance;
    std::map<std::string, std::string> predecessor;
    frontier.push({heuristic(startEdge), startEdge});
    distance[startEdge] = 0;
    RouteResult result;
    while (!frontier.empty()) {
        const auto [priority, id] = frontier.top();
        frontier.pop();
        if (priority > distance[id] + heuristic(id) + 1e-9) continue;
        ++result.expandedNodes;
        if (id == destinationEdge) {
            result.cost = distance[id];
            std::string cursor = id;
            while (cursor != startEdge) {
                result.edges.push_back(cursor);
                cursor = predecessor.at(cursor);
            }
            result.edges.push_back(startEdge);
            std::reverse(result.edges.begin(), result.edges.end());
            if (!graph.connected(result.edges)) throw std::runtime_error("A* produced illegal SUMO turn");
            return result;
        }
        for (const auto& next : graph.successors(id)) {
            const double candidate = distance[id] + edgeCost(graph.edge(next));
            if (!distance.count(next) || candidate < distance[next] - 1e-9) {
                distance[next] = candidate;
                predecessor[next] = id;
                frontier.push({candidate + heuristic(next), next});
            }
        }
    }
    return result;
}

DynamicAStarRouter::DynamicAStarRouter(const RoadGraph& graph,
                                       const std::map<std::string, EdgeObservation>& observations,
                                       double lambda, double capacityPerMeter, int minVehicles)
    : AStarRouter(graph), observations(observations), lambda(lambda), capacityPerMeter(capacityPerMeter), minVehicles(minVehicles)
{
    if (lambda < 0 || capacityPerMeter <= 0) throw std::invalid_argument("Invalid dynamic A* cost parameters");
}

double DynamicAStarRouter::edgeCost(const RoadEdge& edge) const
{
    const auto found = observations.find(edge.id);
    if (found == observations.end() || found->second.vehicleCount < minVehicles) return AStarRouter::edgeCost(edge);
    const auto& observation = found->second;
    const double speed = std::max(observation.meanSpeed, 1.0);
    const double density = std::min(1.0, observation.vehicleCount / (edge.length * capacityPerMeter));
    return (edge.length / speed) * (1.0 + lambda * density);
}

} // namespace emergencynavigation
