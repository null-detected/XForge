
# XForge Config Generator

A high-performance proxy configuration matrix generator for transforming and multiplying proxy configurations across multiple hosts and ports.

This tool takes one or more proxy configuration files and generates combinations by replacing target hosts and ports in supported proxy URIs.

Designed for bulk processing, subnet expansion, and large-scale configuration generation.

## Features

* Supports multiple proxy protocols:

  * `vless://`
  * `vmess://`
  * `trojan://`
  * `ss://`
  * `ssr://`
  * `hysteria://`
  * `hysteria2://`

* Host expansion support:

  * Single IP addresses
  * Domain names
  * CIDR subnets (`192.168.1.0/24`)
  * IPv6 addresses

* Flexible port definitions:

  * Individual ports
  * Comma-separated ports
  * Port ranges

* Multiple input file support

* Duplicate output prevention

* Efficient processing for large datasets

* Automatic subnet size warnings for large ranges

* Processing summary report

## Installation

### Requirements

* Python 3.8+

No third-party dependencies are required.

Clone the repository:

```bash
git clone <your-repository-url>
cd <repository-name>
```

Make the script executable (Linux/macOS):

```bash
chmod +x config-generator.py
```

## Usage

Basic syntax:

```bash
python3 config-generator.py INPUT_FILES --ports PORTS [OPTIONS]
```

### Required Arguments

| Argument  | Description                            |
| --------- | -------------------------------------- |
| `inputs`  | One or more source configuration files |
| `--ports` | Target ports or ranges                 |

### Host Input Options

At least one of the following must be provided:

| Option         | Description                                       |
| -------------- | ------------------------------------------------- |
| `--hosts`      | Inline comma-separated hosts, domains, or subnets |
| `--hosts-file` | File containing hosts                             |

### Optional Arguments

| Option         | Description                                        |
| -------------- | -------------------------------------------------- |
| `-o, --output` | Output file path (default: `ConfigHub_result.txt`) |

## Examples

### Single Host

```bash
python3 config-generator.py config.txt \
  --hosts 1.1.1.1 \
  --ports 443
```

### Multiple Hosts

```bash
python3 config-generator.py config.txt \
  --hosts 1.1.1.1,8.8.8.8,example.com \
  --ports 80,443,8443
```

### Port Range

```bash
python3 config-generator.py config.txt \
  --hosts 1.1.1.1 \
  --ports 8000-8010
```

### CIDR Expansion

```bash
python3 config-generator.py config.txt \
  --hosts 192.168.1.0/24 \
  --ports 443
```

### Hosts File

```bash
python3 config-generator.py config.txt \
  --hosts-file hosts.txt \
  --ports 80,443
```

### Multiple Input Files

```bash
python3 config-generator.py config1.txt config2.txt config3.txt \
  --hosts-file hosts.txt \
  --ports 80,443,8080-8090
```

### Custom Output File

```bash
python3 config-generator.py config.txt \
  --hosts 1.1.1.1 \
  --ports 443 \
  --output generated.txt
```

## Hosts File Format

Example `hosts.txt`:

```txt
1.1.1.1
8.8.8.8
example.com
192.168.1.0/30

# Comments are ignored
```

Comma-separated values are also supported:

```txt
1.1.1.1,8.8.8.8
example.com
```

## How It Works

The tool scans supported proxy URIs in input files and replaces their host and port combinations using the provided targets.

Example input:

```txt
vless://uuid@example.com:443?security=tls
trojan://password@domain.com:443
```

Command:

```bash
python3 config-generator.py config.txt \
  --hosts 1.1.1.1,8.8.8.8 \
  --ports 443,8443
```

Generated output:

```txt
vless://uuid@1.1.1.1:443?security=tls
trojan://password@1.1.1.1:443

vless://uuid@1.1.1.1:8443?security=tls
trojan://password@1.1.1.1:8443

vless://uuid@8.8.8.8:443?security=tls
trojan://password@8.8.8.8:443

vless://uuid@8.8.8.8:8443?security=tls
trojan://password@8.8.8.8:8443
```

## Output Summary

After execution, the tool displays a processing summary including:

* Total lines processed
* Generated configurations
* Skipped lines
* Output location

Example:

```text
==========================================================================
                 Configuration Target Processing Summary
==========================================================================
Filename                  | Total Lines |   Generated |     Skipped
--------------------------------------------------------------------------
config.txt                |          25 |        1000 |            2
==========================================================================
[+] Output compiled successfully. Saved to: output.txt
```

## Notes

* Duplicate configurations are automatically removed.
* Commented lines are ignored.
* Invalid or unsupported proxy lines are skipped.
* Large CIDR ranges trigger a warning to prevent excessive resource usage.
* Output file paths cannot match input file paths.

## License

Add your preferred license here.

