package emergencynavigation.apps;

simple CloudService
{
    @class(emergencynavigation::CloudService);
    string roadNetworkFile = default("grid.net.xml");
    double routeBaseDelay @unit(s) = default(300ms);
    double routeNodeDelay @unit(s) = default(2ms);
    double backhaulDelay @unit(s) = default(150ms);
}
