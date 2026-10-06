# Experiments

SUMO 1.18.0 moves vehicles on a 4 by 4 signalized grid with 48 directed road links. OMNeT++ 6.3.0 and Veins 5.3.1 simulate wireless communication through TraCI. Three RSUs use a 400 m radio neighborhood. Low, medium, and high demand generates 72, 144, and 200 background trips over 360 seconds. Trip generation count differs from the number simultaneously on the road. The collector records peak active background vehicles and unique background vehicles seen up to EV arrival.

The 30 seed labels vary randomTrips demand generation and OMNeT++ random streams. Veins launchd uses the manager's default seed -1, which selects run number zero; SUMO driving randomness therefore uses seed 0 in these runs, overriding the seed written in grid.sumocfg. Different demand seeds still produce different routes and entry edges. Driving randomness is held common rather than independently varied. Varying the SUMO driving seed would define a different experiment and is not silently applied to existing results.

The main comparison is FogCloudAStar, MistAStar, MistDynamicAStar, and MistDynamicFogFallback at three densities and 30 matched seeds (360 runs). A further 90 NoPreemptionBaseline runs use FogCloudAStar routing with signal priority disabled. This control is displayed only for traffic-light waiting time. Its other collected values remain in the individual-run CSV for transparency.


The eight controlled stall seeds and all timing assumptions are specified in METHODOLOGY.md. Normal and stall results are in summary-cohorts.csv. NoPreemptionBaseline appears only in waiting-time summaries and graphs.

## Supplementary route communication and signal validation

The seven headline metrics and the 450-run main matrix are unchanged. Separate route-transaction metrics are derived from original raw scalars, and 18 isolated short-notice red-signal runs validate positive waiting and safe priority transitions. Definitions, confidence intervals, measured tables, and limitations are in [SUPPLEMENTAL_VALIDATION.md](SUPPLEMENTAL_VALIDATION.md).

## Controlled incident and matched recovery evidence

A separate 360-run matrix uses a physical C1C2 stopped queue after initial route selection, with the same incident input and original trips for every algorithm. FCD evidence verifies the incident; all delivered-alert runs must reach the destination. Matched fault recovery is also reported from the original batch. Actual tables, confidence intervals and limits are in [REQUIREMENTS_EVIDENCE.md](REQUIREMENTS_EVIDENCE.md). Shared EM delivery metrics keep their definitions and cannot demonstrate routing superiority. Graph labels retain three decimals for response and waiting; SUMO motion remains sampled every 500 ms.
