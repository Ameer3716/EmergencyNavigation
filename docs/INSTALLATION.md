# Installation

Installation is in progress. The machine audit and current state are recorded in `PROGRESS.md`.

The requested stack is OMNeT++ 6.3.0, Veins 5.3.1, and SUMO 1.18.0. INET 4.6.0 is optional because native Veins IEEE 802.11p is the intended radio model. The official Veins 5.3.1 compatibility list names SUMO 1.18.0 but does not name OMNeT++ 6.3.0. Therefore the stock Veins example build and run are mandatory compatibility checks before custom development. Source: https://veins.car2x.org/download/ .

OMNeT++ recommends `opp_env` for versioned installs under WSL2. Source: https://omnetpp.org/download-items/omnetpp/omnetpp-630.html . Installation commands and any required compatibility patch will be documented after they execute successfully.
