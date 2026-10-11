# Supervisor summary

The experiment was cancelled on 11 October 2026 before reported seeds 1 to 30 began. Updated CSVs include 109 completed held-out pilot runs only: 60 from the 360 second departure window and 49 from the 120 second window. Eleven unfinished or unstarted runs are excluded, with their seed coverage disclosed. No simulations were restarted.

## Preserved complete matched evidence

Baseline is FogCloudAStarAdvance and proposed is MistDynamicFogFallback. Signal request timing is equal.

| Requirement | Ordinary traffic | Fixed obstruction |
| --- | --- | --- |
| A Faster route decision | Supported | Supported |
| B Clear response margin | 0.3 to 0.7 percent; 20 percent reference unmet | About 40 to 45 percent faster |
| C Two additional improvements | Not established | Full stops and background time loss improve |
| D Lower nonzero signal waiting | Both zero; unmet | Paired intervals include zero; not established |

## New pilots and limits

The first pilot formed queues, but baseline response rose only from 148.25 seconds at 400 trips to 150.00 seconds at 600 trips. Its 1.75 second paired increase missed the predeclared 5 second congestion criterion. The stronger-demand pilot was cancelled before completion; its completed subset is descriptive and may have biased completion patterns. It has no completed 600-trip dynamic Fog cell and cannot establish a final ablation or congestion verdict.

Completed pilot response means are higher for the proposed framework in every demand/window comparison, not a response win. Waiting and secondary measures are mixed; the paired intervals and sample counts must be read alongside the means.

The 900 ms stalls remain controlled injected faults. Zero waiting is not altered. Optional signal-aware cost redesign was not adopted. Baselines and reported seeds were not weakened or selected. Full values, paired intervals, counts, coverage and all completed-pilot graphs are in COMPLETED_PILOT_RESULTS.md and results/next_validation/completed_pilots. Preserved reported measurements remain in POLICY_VALIDATION.md.
