# Policy notes — custom client

The policy is called **State-Aware Queue and Cost Heuristic (SAQC)**.

For each incoming job, the client asks the server for the list of capable servers. Each candidate is scored from:
- a state penalty (active/idle servers are preferred to booting/inactive servers);
- an estimated queue penalty based on waiting and running job counts;
- an approximate runtime term adjusted for server type;
- a conservative penalty for using a large server for short jobs.

The client chooses the candidate with the smallest score. This design attempts to reduce turnaround time while avoiding unnecessary server activation and expensive large servers.

The score is heuristic and uses simplified assumptions because the server listing does not directly expose all runtime and pricing information. Evaluate the policy with the official test configs and discuss observed trade-offs honestly.
