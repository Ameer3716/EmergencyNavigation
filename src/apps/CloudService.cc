#include "apps/CloudService.h"

namespace emergencynavigation {
void CloudService::initialize()
{
    graph = std::make_unique<RoadGraph>(par("roadNetworkFile").stdstringValue());
    recordScalar("initialized", 1);
}
RouteResult CloudService::compute(const std::string& startEdge, const std::string& destinationEdge)
{
    return AStarRouter(*graph).route(startEdge, destinationEdge);
}
double CloudService::processingDelay(int expandedNodes) const
{
    return par("routeBaseDelay").doubleValue() + expandedNodes * par("routeNodeDelay").doubleValue();
}
double CloudService::backhaulDelay() const { return par("backhaulDelay").doubleValue(); }
}
Define_Module(emergencynavigation::CloudService);
