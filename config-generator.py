#!/usr/bin/env python3
"""
Proxy Configuration Matrix Generator
Author: Mojtaba @csiseverything
For my friend Ali :)
"""

import argparse
import ipaddress
import re
import sys
from itertools import product
from pathlib import Path
from typing import Generator, Iterable, List, Set, Tuple


class ProxyMatrixGenerator:
    PROXY_URI_PATTERN = re.compile(
        r"((?:vless|vmess|trojan|ss|ssr|hysteria2?)://(?:[^@]*@)?)"
        r"(\[[\da-fA-F:]+\]|[^:/?#\s]+)"
        r":(\d+)"
    )
    LARGE_SUBNET_THRESHOLD = 65536

    def __init__(self, ports_spec: str, hosts_spec: str = None, hosts_file: str = None):
        self.ports: List[str] = [str(p) for p in self._parse_ports(ports_spec)]
        self.hosts: List[str] = [self._format_host(h) for h in self._parse_hosts(hosts_spec, hosts_file)]
        
        if not self.ports:
            raise ValueError("No valid ports could be resolved from the provided specification.")
        if not self.hosts:
            raise ValueError("No valid target hosts could be resolved.")

    def _parse_ports(self, spec: str) -> List[int]:
        resolved_ports: List[int] = []
        seen: Set[int] = set()

        for chunk in spec.split(","):
            chunk = chunk.strip()
            if not chunk:
                continue

            if "-" in chunk:
                try:
                    start_str, end_str = chunk.split("-", 1)
                    start, end = int(start_str.strip()), int(end_str.strip())
                except ValueError:
                    raise ValueError(f"Malformed port range expression: '{chunk}'")

                if not (1 <= start <= 65535 and 1 <= end <= 65535) or start > end:
                    raise ValueError(f"Port range out of bounds or inverted: '{chunk}'")

                for port in range(start, end + 1):
                    if port not in seen:
                        resolved_ports.append(port)
                        seen.add(port)
            else:
                try:
                    port = int(chunk)
                except ValueError:
                    raise ValueError(f"Invalid integer port value: '{chunk}'")
                
                if not (1 <= port <= 65535):
                    raise ValueError(f"Port {port} sits outside valid range [1-65535]")
                if port not in seen:
                    resolved_ports.append(port)
                    seen.add(port)

        return resolved_ports

    def _format_host(self, host: str) -> str:
        try:
            if ipaddress.ip_address(host).version == 6:
                return f"[{host}]"
        except ValueError:
            pass
        return host

    def _expand_target(self, token: str) -> Generator[str, None, None]:
        try:
            network = ipaddress.ip_network(token, strict=False)
            if network.num_addresses > self.LARGE_SUBNET_THRESHOLD:
                print(f" -> [!] Warning: '{token}' contains {network.num_addresses:,} hosts. Expect high disk usage.")
            for ip in network.hosts():
                yield str(ip)
        except ValueError:
            yield token

    def _parse_hosts(self, spec: str = None, file_path: str = None) -> List[str]:
        unique_hosts: List[str] = []
        seen: Set[str] = set()

        def append_host(h: str):
            if h not in seen:
                unique_hosts.append(h)
                seen.add(h)

        if spec:
            for piece in spec.split(","):
                piece = piece.strip()
                if piece:
                    for expanded in self._expand_target(piece):
                        append_host(expanded)

        if file_path:
            p = Path(file_path)
            if not p.is_file():
                print(f"[-] Error: Target hosts file not found at '{file_path}'", file=sys.stderr)
                sys.exit(1)
            
            with p.open("r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    for piece in line.split(","):
                        piece = piece.strip()
                        if piece:
                            for expanded in self._expand_target(piece):
                                append_host(expanded)

        return unique_hosts

    def transform_file(self, input_path: Path, out_stream) -> Tuple[int, int, int]:
        with input_path.open("r", encoding="utf-8-sig") as f:
            lines = [ln.strip() for ln in f if ln.strip()]

        active_proxies = [ln for ln in lines if not ln.startswith("#") and self.PROXY_URI_PATTERN.search(ln)]
        skipped_count = len(lines) - len(active_proxies)
        
        if not active_proxies:
            return len(lines), 0, skipped_count

        written_count = 0
        emitted_lines: Set[str] = set()

        for h, p in product(self.hosts, self.ports):
            chunk: List[str] = []
            for base_line in active_proxies:
                altered = self.PROXY_URI_PATTERN.sub(lambda m: f"{m.group(1)}{h}:{p}", base_line)
                if altered not in emitted_lines:
                    chunk.append(altered)
                    emitted_lines.add(altered)
            if chunk:
                out_stream.write("\n".join(chunk) + "\n")
                written_count += len(chunk)

        return len(lines), written_count, skipped_count


def display_report(metrics: List[dict], output_target: Path):
    print("\n" + "="*74)
    print(f"{'Configuration Target Processing Summary':^74}")
    print("="*74)
    print(f"{'Filename':<25} | {'Total Lines':>11} | {'Generated':>11} | {'Skipped':>11}")
    print("-"*74)

    t_lines = t_gen = t_skip = 0
    for row in metrics:
        print(f"{row['file']:<25} | {row['total']:>11,} | {row['gen']:>11,} | {row['skip']:>11,}")
        t_lines += row['total']
        t_gen += row['gen']
        t_skip += row['skip']

    if len(metrics) > 1:
        print("-"*74)
        print(f"{'TOTALS':<25} | {t_lines:>11,} | {t_gen:>11,} | {t_skip:>11,}")
    print("="*74)
    print(f"[+] Output compiled successfully. Saved to: {output_target}\n")


def main():
    parser = argparse.ArgumentParser(description="Proxy Payload Configuration Multiplexer")
    parser.add_argument("inputs", nargs="+", help="Source configuration files containing template URIs.")
    parser.add_argument("-o", "--output", default="ConfigHub_result.txt", help="Destination path for compilation matrix.")
    parser.add_argument("--hosts", help="Inline comma-delimited strings of IPs, subnets, or hostnames.")
    parser.add_argument("--hosts-file", help="Filepath containing line-separated targets.")
    parser.add_argument("--ports", required=True, help="Target ports or ranges (e.g., 80,443,8000-8010).")
    
    args = parser.parse_args()

    if not args.hosts and not args.hosts_file:
        parser.error("Execution requires either --hosts or --hosts-file parameter values.")

    try:
        engine = ProxyMatrixGenerator(ports_spec=args.ports, hosts_spec=args.hosts, hosts_file=args.hosts_file)
    except ValueError as err:
        print(f"[-] Operational Error: {err}", file=sys.stderr)
        sys.exit(1)

    input_paths = [Path(i) for i in args.inputs]
    for ipath in input_paths:
        if not ipath.is_file():
            print(f"[-] Source reference not found: '{ipath}'", file=sys.stderr)
            sys.exit(1)

    dest_path = Path(args.output).resolve()
    if any(src.resolve() == dest_path for src in input_paths):
        print("[-] Conflict Avoidance: Output location matches an input file path. Aborting.", file=sys.stderr)
        sys.exit(1)

    print(f"[+] Multiplier processing initialized ({len(engine.hosts):,} hosts x {len(engine.ports):,} ports)")
    
    run_summary = []
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with dest_path.open("w", encoding="utf-8", buffering=1024 * 1024) as out:
            for ipath in input_paths:
                print(f" -> Mapping: {ipath.name}...")
                total, gen, skip = engine.transform_file(ipath, out)
                run_summary.append({'file': ipath.name, 'total': total, 'gen': gen, 'skip': skip})
    except OSError as err:
        print(f"[-] Disk Write Failure: {err}", file=sys.stderr)
        sys.exit(1)

    display_report(run_summary, dest_path)


if __name__ == "__main__":
    main()
