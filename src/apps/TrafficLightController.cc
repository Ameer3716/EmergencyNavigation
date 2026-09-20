#include <omnetpp.h>

namespace emergencynavigation {
class TrafficLightController : public omnetpp::cSimpleModule {
protected:
    void initialize() override { recordScalar("initialized", 1); }
    void handleMessage(omnetpp::cMessage* message) override { delete message; }
};
}
Define_Module(emergencynavigation::TrafficLightController);
