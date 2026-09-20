package emergencynavigation.apps;

simple FogService
{
    @class(emergencynavigation::FogService);
    string roadNetworkFile = default("grid.net.xml");
    double routeBaseDelay @unit(s) = default(300ms);
    double routeNodeDelay @unit(s) = default(2ms);
    double densityLambda = default(0.5);
    double serviceRadius @unit(m) = default(500m);
}
