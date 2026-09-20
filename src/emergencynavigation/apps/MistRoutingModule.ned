package emergencynavigation.apps;

simple MistRoutingModule
{
    @class(emergencynavigation::MistRoutingModule);
    string roadNetworkFile = default("grid.net.xml");
    bool available = default(true);
    double densityLambda = default(0.5);
    double routeBaseDelay @unit(s) = default(300ms);
    double routeNodeDelay @unit(s) = default(2ms);
}
