# Experiments

SUMO 1.18.0 moves vehicles on a 4 by 4 signalized grid with 48 directed road links. OMNeT++ 6.3.0 and Veins 5.3.1 simulate wireless communication through TraCI. Three RSUs use a 400 m radio neighborhood. Low, medium, and high demand generates 72, 144, and 200 background trips over 360 seconds. Trip generation count differs from the number simultaneously on the road. The collector records peak active background vehicles and unique background vehicles seen up to EV arrival.

The main comparison is FogCloudAStar, MistAStar, MistDynamicAStar, and MistDynamicFogFallback at three densities and 30 matched seeds (360 runs). A further 90 NoPreemptionBaseline runs use FogCloudAStar routing with signal priority disabled. This control is displayed only for traffic-light waiting time. Its other collected values remain in the individual-run CSV for transparency.


The eight controlled stall seeds and all timing assumptions are specified in METHODOLOGY.md. Normal and stall results are in summary-cohorts.csv. NoPreemptionBaseline appears only in waiting-time summaries and graphs.
