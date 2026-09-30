# JOCKY Forensic IR Specification v1.1
## SIH26148 — Intermediate Representation Format

---

## 1. Overview

The JOCKY Forensic IR is a JSON-based intermediate representation that describes forensic investigation workflows in a platform-independent format. It is the sole contract between the JOCKY compiler and the IR execution engine.

## 2. Top-Level Structure

```json
{
  "version": "1.1",
  "type": "ir_program",
  "case_id": "string | null",
  "investigation": "string",
  "script_hash": "SHA-256 of source",
  "compiler_version": "1.0.0",
  "build_id": "UUID",
  "build_profile": "forensic_standard | forensic_hardened | forensic_variant",
  "generated_at": "ISO-8601 timestamp",
  "required_capabilities": ["PROCESS_READ", "NETWORK_READ", ...],
  "scopes": [IRScope, ...]
}
```

## 3. IR Scope

```json
{
  "scope_type": "investigation | host",
  "name": "string",
  "target_host": "hostname | null",
  "operations": [IROperation, ...]
}
```

## 4. IR Operations

### 4.1 COLLECT
```json
{
  "op": "COLLECT",
  "target": "PROCESSES | NETWORK_CONNECTIONS | SYSTEM_INFO | FILE_HASH | EVENT_LOGS | PERSISTENCE | FILESYSTEM",
  "arguments": {
    "paths": ["optional file paths for FILE_HASH"],
    "filters": {}
  }
}
```

Required capability mapping:
| Target | Capability |
|---|---|
| PROCESSES | PROCESS_READ |
| NETWORK_CONNECTIONS | NETWORK_READ |
| SYSTEM_INFO | SYSTEM_INFO_READ |
| FILE_HASH | FILE_READ, FILE_HASH |
| EVENT_LOGS | EVENT_LOG_READ |
| PERSISTENCE | PERSISTENCE_READ |
| FILESYSTEM | FILE_READ |

### 4.2 ANALYZE
```json
{
  "op": "ANALYZE",
  "target": "PROCESSES | NETWORK_CONNECTIONS | PERSISTENCE",
  "arguments": {}
}
```

### 4.3 FILTER
```json
{
  "op": "FILTER",
  "target": "PROCESSES | NETWORK_CONNECTIONS | ...",
  "arguments": {
    "condition": {
      "field": "string",
      "operator": "> | < | >= | <= | == | != | in",
      "value": "number | string | [array]"
    }
  }
}
```

### 4.4 GENERATE_TIMELINE
```json
{
  "op": "GENERATE_TIMELINE",
  "arguments": {}
}
```

### 4.5 GENERATE_REPORT
```json
{
  "op": "GENERATE_REPORT",
  "arguments": {
    "format": "json | csv | pdf"
  }
}
```

## 5. Capabilities

The IR declares required capabilities in `required_capabilities`. The policy engine validates these before execution.

| Capability | Description | Risk |
|---|---|---|
| PROCESS_READ | Enumerate running processes | Low |
| NETWORK_READ | Enumerate network connections | Low |
| SYSTEM_INFO_READ | Read system information | Low |
| FILE_READ | Read file metadata | Low |
| FILE_HASH | Compute file hashes | Low |
| EVENT_LOG_READ | Read OS event logs | Low |
| PERSISTENCE_READ | Enumerate persistence mechanisms | Low |

## 6. Execution Contract

1. The IR executor MUST consume only the operations listed in the IR.
2. The IR executor MUST NOT execute operations not present in the IR.
3. Each COLLECT operation maps to exactly one platform-specific collector.
4. FILTER operations are applied post-collection to reduce evidence sets.
5. ANALYZE operations trigger the rule engine on collected evidence.
6. GENERATE operations produce output artifacts.

## 7. Evidence Output Format

Each collector produces evidence in the normalized format:
```json
{
  "evidence_id": "UUID",
  "case_id": "string",
  "execution_id": "UUID",
  "host_id": "UUID",
  "collector": "process | network | system | filesystem",
  "collector_version": "1.0.0",
  "platform": "windows | linux",
  "type": "PROCESS | NETWORK_CONNECTION | SYSTEM_INFO | FILE_METADATA",
  "collected_at": "ISO-8601",
  "payload": { ... }
}
```
