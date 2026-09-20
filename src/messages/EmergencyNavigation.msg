import veins.modules.messages.BaseFrame1609_4;

namespace emergencynavigation;

packet EmergencyMessage extends veins::BaseFrame1609_4
{
    string eventId;
    string messageId;
    double generationTimestamp;
    double accidentX;
    double accidentY;
    string senderId;
    int remainingHops;
    int hopCount;
    int payloadBytes;
}

packet TrafficBeacon extends veins::BaseFrame1609_4
{
    string vehicleId;
    double positionX;
    double positionY;
    double speed;
    string currentEdge;
    double timestamp;
}

packet TrafficStatus extends veins::BaseFrame1609_4
{
    string edgeId;
    int vehicleCount;
    double meanSpeed;
    double timestamp;
}

packet RouteRequest extends veins::BaseFrame1609_4
{
    string requestId;
    string emergencyVehicleId;
    string startEdge;
    string destinationEdge;
    double startX;
    double startY;
    double accidentX;
    double accidentY;
    double requestTimestamp;
    string edgeCosts;
}

packet RouteReply extends veins::BaseFrame1609_4
{
    string requestId;
    string routeEdges;
    double estimatedCost;
    string computationLocation;
    double computationStarted;
    double computationFinished;
    bool routeValid;
}

packet CloudRouteRequest extends veins::BaseFrame1609_4
{
    string requestId;
    string startEdge;
    string destinationEdge;
    string edgeCosts;
    double requestTimestamp;
}

packet CloudRouteReply extends veins::BaseFrame1609_4
{
    string requestId;
    string routeEdges;
    double estimatedCost;
    double computationStarted;
    double computationFinished;
    bool routeValid;
}

packet TLPreemptionRequest extends veins::BaseFrame1609_4
{
    string emergencyVehicleId;
    string trafficLightId;
    string incomingEdge;
    double positionX;
    double positionY;
    double speed;
    double eta;
    double timestamp;
}

packet TLPreemptionGrant extends veins::BaseFrame1609_4
{
    string emergencyVehicleId;
    string trafficLightId;
    double requestTimestamp;
    double greenActivationTimestamp;
    bool granted;
}

packet TLPreemptionRelease extends veins::BaseFrame1609_4
{
    string emergencyVehicleId;
    string trafficLightId;
    double timestamp;
}
