#include "apps/FogService.h"

#include <cmath>

namespace emergencynavigation {
void FogService::initialize()
{
    graph = std::make_unique<RoadGraph>(par("roadNetworkFile").stdstringValue());
    recordScalar("initialized", 1);
}
RouteResult FogService::compute(const std::string& startEdge, const std::string& destinationEdge,
                                const std::map<std::string, EdgeObservation>& observations, bool dynamic)
{
    return dynamic ? DynamicAStarRouter(*graph, observations, par("densityLambda")).route(startEdge, destinationEdge)
                   : AStarRouter(*graph).route(startEdge, destinationEdge);
}
double FogService::processingDelay(int expandedNodes) const
{
    return par("routeBaseDelay").doubleValue() + expandedNodes * par("routeNodeDelay").doubleValue();
}
bool FogService::withinServiceArea(double x, double y) const
{
    const auto center = getParentModule()->getSubmodule("mobility");
    if (!center) throw omnetpp::cRuntimeError("Fog RSU has no mobility module");
    const double dx = center->par("x").doubleValue() - x;
    const double dy = center->par("y").doubleValue() - y;
    return std::hypot(dx, dy) <= par("serviceRadius").doubleValue();
}
}
Define_Module(emergencynavigation::FogService);
