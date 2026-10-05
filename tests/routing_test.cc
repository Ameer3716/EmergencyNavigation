#include "routing/AStarRouter.h"
#include <cassert>
#include <iostream>

using namespace emergencynavigation;

int main(int argc, char** argv)
{
    if (argc != 2) return 2;
    RoadGraph graph(argv[1]);
    assert(graph.edgeCount() == 48);
    auto staticRoute = AStarRouter(graph).route("A0A1", "D2D3");
    assert(graph.connected(staticRoute.edges));
    assert(staticRoute.edges.front() == "A0A1" && staticRoute.edges.back() == "D2D3");
    std::map<std::string, EdgeObservation> congestion;
    congestion["C1C2"] = {12, 1.0, 100};
    auto dynamicRoute = DynamicAStarRouter(graph, congestion, 0.5).route("A0A1", "D2D3");
    assert(graph.connected(dynamicRoute.edges));
    assert(staticRoute.edges != dynamicRoute.edges);
    std::map<std::string, EdgeObservation> speeding;
    for (const auto& edge : staticRoute.edges) speeding[edge] = {3, 100.0, 100};
    const auto cappedRoute = DynamicAStarRouter(graph, speeding, 0.5).route("A0A1", "D2D3");
    assert(cappedRoute.cost >= staticRoute.cost - 1e-9);
    std::cout << "static=";
    for (const auto& edge : staticRoute.edges) std::cout << edge << ' ';
    std::cout << "\ndynamic=";
    for (const auto& edge : dynamicRoute.edges) std::cout << edge << ' ';
    std::cout << "\nexpanded=" << staticRoute.expandedNodes << ',' << dynamicRoute.expandedNodes << '\n';
}
