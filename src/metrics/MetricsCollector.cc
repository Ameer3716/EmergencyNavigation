#include <omnetpp.h>

namespace emergencynavigation {
class MetricsCollector : public omnetpp::cSimpleModule {
protected:
    void initialize() override { recordScalar("initialized", 1); }
    void handleMessage(omnetpp::cMessage* message) override { delete message; }
};
}
Define_Module(emergencynavigation::MetricsCollector);
