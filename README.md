# Emergency vehicle navigation simulation

SUMO, OMNeT++, and Veins model accident alert delivery and emergency vehicle routing on a signalized grid. The main comparison contains FogCloudAStar, MistAStar, MistDynamicAStar, and MistDynamicFogFallback (360 matched runs). A further 90 NoPreemptionBaseline runs appear only in the traffic-light waiting comparison.

The [Word report](docs/Emergency_Vehicle_Navigation_Final_Submission.docx) explains the system in plain English and contains every graph. The [graph guide](docs/PROCESS_AND_GRAPHS.md) displays them on GitHub. See [methodology](docs/METHODOLOGY.md), [measured verification](docs/VERIFICATION.md), and [installation](docs/INSTALLATION.md).

The watchdog is 500 ms and the telemetry delay is 0 ms. Eight of 30 seeds are explicitly labeled controlled Mist stalls, applied to every Mist approach for fairness. Normal and controlled results are available separately in results/processed/summary-cohorts.csv. Equal PDR or EM throughput can be valid because the alert precedes route computation and has a fixed payload/window.
