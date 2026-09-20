#include "routing/RoadGraph.h"

#include <algorithm>
#include <fstream>
#include <regex>
#include <stdexcept>

namespace emergencynavigation {

static std::string attribute(const std::string& tag, const char* name)
{
    const std::regex pattern(std::string(name) + "=\"([^\"]*)\"");
    std::smatch match;
    return std::regex_search(tag, match, pattern) ? match[1].str() : "";
}

RoadGraph::RoadGraph(const std::string& netXml)
{
    std::ifstream file(netXml);
    if (!file) throw std::runtime_error("Cannot open SUMO road network: " + netXml);
    std::string line;
    RoadEdge pending;
    bool inEdge = false;
    while (std::getline(file, line)) {
        if (line.find("<junction ") != std::string::npos) {
            const auto id = attribute(line, "id");
            if (!id.empty() && id[0] != ':')
                junctions[id] = {std::stod(attribute(line, "x")), std::stod(attribute(line, "y"))};
        }
        if (line.find("<connection ") != std::string::npos) {
            const auto from = attribute(line, "from");
            const auto to = attribute(line, "to");
            if (!from.empty() && !to.empty() && from[0] != ':' && to[0] != ':') {
                auto& next = transitions[from];
                if (std::find(next.begin(), next.end(), to) == next.end()) next.push_back(to);
            }
        }
        if (line.find("<edge ") != std::string::npos) {
            pending = {};
            pending.id = attribute(line, "id");
            pending.from = attribute(line, "from");
            pending.to = attribute(line, "to");
            inEdge = !pending.id.empty() && pending.id[0] != ':' && !pending.from.empty() && !pending.to.empty();
        }
        if (inEdge && line.find("<lane ") != std::string::npos && pending.length == 0) {
            pending.length = std::stod(attribute(line, "length"));
            pending.speedLimit = std::stod(attribute(line, "speed"));
        }
        if (inEdge && line.find("</edge>") != std::string::npos) {
            if (pending.length <= 0 || pending.speedLimit <= 0)
                throw std::runtime_error("Invalid SUMO edge: " + pending.id);
            maxSpeed = std::max(maxSpeed, pending.speedLimit);
            adjacency[pending.from].push_back(pending.id);
            edges.emplace(pending.id, pending);
            inEdge = false;
        }
    }
    if (edges.empty() || junctions.empty()) throw std::runtime_error("SUMO network contains no routable edges or junctions");
}

const RoadEdge& RoadGraph::edge(const std::string& id) const
{
    return edges.at(id);
}

const std::vector<std::string>& RoadGraph::outgoing(const std::string& node) const
{
    static const std::vector<std::string> empty;
    const auto found = adjacency.find(node);
    return found == adjacency.end() ? empty : found->second;
}

const Junction& RoadGraph::junction(const std::string& id) const
{
    return junctions.at(id);
}

const std::vector<std::string>& RoadGraph::successors(const std::string& edgeId) const
{
    static const std::vector<std::string> empty;
    const auto found = transitions.find(edgeId);
    return found == transitions.end() ? empty : found->second;
}

bool RoadGraph::connected(const std::vector<std::string>& route) const
{
    if (route.empty()) return false;
    try {
        for (size_t i = 1; i < route.size(); ++i)
            if (std::find(successors(route[i - 1]).begin(), successors(route[i - 1]).end(), route[i]) == successors(route[i - 1]).end()) return false;
    } catch (const std::out_of_range&) { return false; }
    return true;
}

} // namespace emergencynavigation
