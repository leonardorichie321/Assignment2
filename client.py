#!/usr/bin/env python3
"""COMP8110 Assignment 2 scheduling client (Python 3).

Uses the ds-sim text protocol with newline-terminated messages. The policy
prefers currently usable servers and estimates queue delay from the server
state and queued/running job counts, while accounting for server speed and
boot-up delay. It is a heuristic; evaluate and tune against the supplied tests.
"""
import argparse
import socket
import sys
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ServerInfo:
    server_type: str
    server_id: int
    state: str
    time_value: int
    free_cores: int
    free_memory: int
    free_disk: int
    waiting_jobs: int
    running_jobs: int

    @property
    def jobs(self) -> int:
        return self.waiting_jobs + self.running_jobs


def recv_line(reader) -> str:
    raw = reader.readline()
    if not raw:
        raise ConnectionError("ds-server closed the connection")
    return raw.decode("utf-8", errors="replace").strip()


def send_line(sock: socket.socket, message: str) -> None:
    sock.sendall((message + "\n").encode("utf-8"))


def get_server_list(sock, reader, cores: int, memory: int, disk: int) -> List[ServerInfo]:
    send_line(sock, f"GETS Capable {cores} {memory} {disk}")
    header = recv_line(reader)
    parts = header.split()
    if len(parts) < 2 or parts[0] != "DATA":
        return []
    count = int(parts[1])
    send_line(sock, "OK")
    rows = []
    for _ in range(count):
        line = recv_line(reader)
        cols = line.split()
        if len(cols) < 9:
            continue
        try:
            rows.append(ServerInfo(
                server_type=cols[0], server_id=int(cols[1]), state=cols[2],
                time_value=int(cols[3]), free_cores=int(cols[4]),
                free_memory=int(cols[5]), free_disk=int(cols[6]),
                waiting_jobs=int(cols[7]), running_jobs=int(cols[8])))
        except ValueError:
            continue
    send_line(sock, "OK")
    # ds-sim ends the list with a dot line.
    terminator = recv_line(reader)
    if terminator != ".":
        # Keep the protocol in sync if a server version includes an extra line.
        while terminator and terminator != ".":
            terminator = recv_line(reader)
    return rows


def choose_server(servers: List[ServerInfo], job_cores: int, job_mem: int,
                  job_disk: int, est_runtime: int) -> Optional[ServerInfo]:
    feasible = [s for s in servers if s.free_cores >= job_cores
                and s.free_memory >= job_mem and s.free_disk >= job_disk]
    if not feasible:
        # Capable query should filter by capacity; this fallback is defensive.
        feasible = [s for s in servers if s.free_memory >= job_mem and s.free_disk >= job_disk]
    if not feasible:
        return None

    # Lower score is better. Prefer active/idle servers with available capacity;
    # avoid waking an inactive server when an already active one can run the job.
    state_penalty = {"active": 0.0, "idle": 0.5, "booting": 60.0, "inactive": 75.0}
    candidates = []
    for s in feasible:
        penalty = state_penalty.get(s.state.lower(), 30.0)
        # Extra queued/running work is a rough estimate of contention.
        queue_penalty = s.jobs * max(1.0, est_runtime * 0.65)
        # Higher-capacity types tend to run jobs faster, but don't pay for a large
        # server unless it has a useful speed/queue advantage.
        type_speed = {"small": 1.0, "medium": 1.2, "large": 1.4}
        speed = type_speed.get(s.server_type.lower(), 1.0)
        predicted = (penalty + queue_penalty + est_runtime / speed)
        # A currently active server with spare cores receives a small preference.
        if s.state.lower() == "active" and s.free_cores >= job_cores:
            predicted -= 8.0
        # Penalise using a large server for short jobs to limit rental cost.
        if s.server_type.lower() == "large" and est_runtime < 300:
            predicted += 20.0
        candidates.append((predicted, s.server_type, s.server_id, s))
    candidates.sort(key=lambda x: (x[0], x[1], x[2]))
    return candidates[0][3]


def run(host: str, port: int) -> int:
    with socket.create_connection((host, port), timeout=15) as sock:
        sock.settimeout(120)
        reader = sock.makefile("rb")
        send_line(sock, "HELO")
        if recv_line(reader) != "OK":
            return 1
        # The reference client authenticates with the current username.
        import getpass
        send_line(sock, "AUTH " + getpass.getuser())
        if recv_line(reader) != "OK":
            return 1

        while True:
            send_line(sock, "REDY")
            message = recv_line(reader)
            if message == "NONE":
                send_line(sock, "QUIT")
                # Consume server acknowledgement when present.
                try:
                    recv_line(reader)
                except Exception:
                    pass
                return 0
            fields = message.split()
            if not fields:
                continue
            if fields[0] == "JCPL":
                continue
            if fields[0] != "JOBN" or len(fields) < 7:
                # Unknown informational message: request the next event.
                continue

            job_id = int(fields[1])
            job_cores, job_mem, job_disk = map(int, fields[3:6])
            est_runtime = int(fields[6])
            servers = get_server_list(sock, reader, job_cores, job_mem, job_disk)
            chosen = choose_server(servers, job_cores, job_mem, job_disk, est_runtime)
            if chosen is None:
                # Avoid malformed scheduling commands; request next event.
                continue
            send_line(sock, f"SCHD {job_id} {chosen.server_type} {chosen.server_id}")
            reply = recv_line(reader)
            if reply != "OK":
                # A scheduling failure is not fatal; continue to next event.
                continue


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50000)
    args = parser.parse_args()
    try:
        sys.exit(run(args.host, args.port))
    except (OSError, ConnectionError, ValueError) as exc:
        print(f"client error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
