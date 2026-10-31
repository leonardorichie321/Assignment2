# COMP8110 Assignment 2 — Scheduling Client

This folder contains the supplied `ds-test` simulator/testing package plus `client.py`,
a Python scheduling client that speaks the newline-terminated ds-sim protocol.

## Included
- `client.py` — custom scheduling policy and ds-sim protocol handling
- `ds-server`, `ds-client` — binaries from the provided archive
- `ds_test.py`, `mark_client.py`, `ref_results.py` — supplied testing/marking scripts
- `TestConfigs/`, `PrelimConfigs/` — supplied simulation configurations
- `results/ref_results.json` — supplied reference results

## Run (Linux / WSL)
The supplied `ds-server` and `ds-client` are Linux ELF executables. On Windows, use WSL (Ubuntu) or a Linux environment.

Install Python 3 if needed, then open a terminal in this folder and run:

```bash
python3 ds_test.py "python3 client.py --port 50000" -n -p 50000 -c PrelimConfigs
```

To run the full supplied test set:

```bash
python3 ds_test.py "python3 client.py --port 50000" -n -p 50000 -c TestConfigs
```

Use a port that is free on your machine. If you change it, change it in both `--port` for the client and `-p` for `ds_test.py`.

## Scheduling policy
The client uses a heuristic that:
1. queries servers capable of running each job;
2. estimates relative delay from server state and queued/running job counts;
3. accounts for approximate server speed and avoids large servers for short jobs;
4. schedules the job to the lowest-scoring candidate.

This is a heuristic, not a proof of optimality. The supplied preliminary configurations were run successfully with the client; performance varies by workload. Do not treat preliminary results as results for all `TestConfigs`, and do not claim the policy beats every baseline unless the full test output supports that.

## Academic integrity
This is a starter implementation for you to review, understand, test, and adapt. Your assignment is individual work. Follow the unit's rules and include a truthful Generative AI Usage Disclosure in the report, including links to relevant usage, as required by the assignment brief.
