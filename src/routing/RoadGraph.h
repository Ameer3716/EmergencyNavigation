#pragma once

#include <map>
#include <string>
#include <vector>

namespace emergencynavigation {

struct RoadEdge {
    std::string id, from, to;
    double length = 0;
    double speedLimit = 0;
};

struct Junction { double x = 0, y = 0; };

class RoadGraph {
public:
    explicit RoadGraph(const std::string& netXml);
    const RoadEdge& edge(const std::string& id) const;
    const std::vector<std::string>& outgoing(const std::string& node) const;
    const std::vector<std::string>& successors(const std::string& edgeId) const;
    const Junction& junction(const std::string& id) const;
    double maximumSpeed() const { return maxSpeed; }
    size_t edgeCount() const { return edges.size(); }
    bool connected(const std::vector<std::string>& route) const;
private:
    std::map<std::string, RoadEdge> edges;
    std::map<std::string, std::vector<std::string>> adjacency;
    std::map<std::string, std::vector<std::string>> transitions;
    std::map<std::string, Junction> junctions;
    double maxSpeed = 0;
};

} // namespace emergencynavigation
