#include "apps/MistRoutingModule.h"

namespace emergencynavigation {
void MistRoutingModule::initialize()
{
    graph = std::make_unique<RoadGraph>(par("roadNetworkFile").stdstringValue());
    recordScalar("initialized", 1);
}
RouteResult MistRoutingModule::compute(const std::string& startEdge, const std::string& destinationEdge,
                                        const std::map<std::string, EdgeObservation>& observations, bool dynamic)
{
    if (!par("available").boolValue()) return {};
    return dynamic ? DynamicAStarRouter(*graph, observations, par("densityLambda"), 1.0 / 7.5, par("minimumObservedVehicles").intValue()).route(startEdge, destinationEdge)
                   : AStarRouter(*graph).route(startEdge, destinationEdge);
}
double MistRoutingModule::processingDelay(int expandedNodes) const
{
    return par("routeBaseDelay").doubleValue() + expandedNodes * par("routeNodeDelay").doubleValue();
}
}
Define_Module(emergencynavigation::MistRoutingModule);
