# Predator Hunt Arsenale Omnibus - Code Review Report

## Overview

Full code review and improvement of `src/predator_arsenale.py`, an 18-module
forensic analysis tool designed for Android/Termux environments.

**Reviewed by:** Claude (Sorella)
**Date:** 2026-03-10
**Status:** Fixed and improved - all modules preserved at full power

---

## Bugs Fixed (Critical)

| # | Issue | Severity | Fix |
|---|-------|----------|-----|
| 1 | `PSUTIL_AVAILABLE` never defined | **CRASH** | Added proper `try/except ImportError` block |
| 2 | `subprocess.run(cmd, shell=True)` with unsanitised path in `VideoAnalyzer._extract_frames` | **Command Injection** | Changed to `subprocess.run([...])` with argument list |
| 3 | Bare `except:` in all 18 modules (catches `SystemExit`, `KeyboardInterrupt`) | **Bug Hiding** | Replaced with specific exception types |
| 4 | `hashlib.md5(os.urandom(16))` for artifact IDs | **Weak IDs** | Replaced with `uuid.uuid4().hex[:16]` |
| 5 | DB connections not closed on error | **DB Lock** | Added `with sqlite3.connect()` context managers |
| 6 | `os.makedirs` / `os.geteuid` called at module import time | **Import Crash** | Moved to lazy initialisation in `_ensure_dirs()` |
| 7 | `datetime.now()` without timezone (naive datetimes) | **Data Quality** | All timestamps now use `timezone.utc` |
| 8 | `INSERT INTO artifacts` without `OR IGNORE` | **Duplicate Key Crash** | Added `INSERT OR IGNORE` |

## Code Quality Improvements

| # | Issue | Fix |
|---|-------|-----|
| 1 | 13 unused imports (`pickle`, `socket`, `ssl`, `wave`, `io`, `mmap`, `zlib`, `binascii`, `numpy`, `numba`, `deque`, `struct`, `Counter`) | Removed |
| 2 | Shannon entropy duplicated in `StegoHunter` and `VideoAnalyzer` | Extracted to shared `shannon_entropy()` function |
| 3 | `uvloop.set_event_loop_policy()` as module-level side effect | Removed (user can set this externally) |
| 4 | No type hints on most methods | Added full type annotations |
| 5 | No docstrings on many methods | Added comprehensive docstrings |
| 6 | `self.frida` shadows the `frida` module import | Renamed to `self.frida_mod` |
| 7 | `aiofiles` used without fallback when not installed | Added sync fallback via `_read_file_bytes`/`_read_file_text` helpers |
| 8 | Magic number `50*1024*1024` for max file size | Made into class constant `BulkExtractor.MAX_FILE_SIZE` |

## Architecture Improvements

| # | Change | Rationale |
|---|--------|-----------|
| 1 | `output_dir` is now a constructor parameter | Testable, no global state |
| 2 | `quarantine_dir` derived from `output_dir` | Single source of truth |
| 3 | Scan pipeline split into named `_run_*` methods | Readable, individually testable |
| 4 | CLI supports `--output-dir` flag | Configurable without code changes |
| 5 | `--apk` and `--pcap` now support `action="append"` | Multiple files per invocation |
| 6 | `build_parser()` extracted for testability | Follows project convention |

## Modules Preserved (Full Power)

All 18 modules retained with identical capabilities:

1. **YaraEngine** - Malware signature scanning (4 rules)
2. **NetworkArsenal** - Live capture + PCAP image carving
3. **MemoryForensics** - /proc/kcore dump + secret pattern matching
4. **FridaDynamic** - Runtime instrumentation (getDeviceId hook)
5. **RadareAnalyzer** - Binary URL extraction via r2pipe
6. **AndroAnalyzer** - APK permissions/activities via AndroGuard
7. **BulkExtractor** - Email, crypto, phone, URL, GPS extraction
8. **DatabaseForensics** - SQLite suspicious table detection
9. **TLSFingerprint** - JA3 malware fingerprint lookup
10. **BehavioralML** - CPU/memory anomaly detection
11. **QEMUSandbox** - Dynamic analysis placeholder
12. **StegoHunter** - JPEG EOF analysis, stego signatures, entropy
13. **VaultHunter** - Hidden apps, suspicious dirs, double extensions
14. **PerceptualHunter** - Image duplicate detection via ahash
15. **VideoAnalyzer** - Format detection, entropy, frame extraction
16. **BlockchainAnalyzer** - BTC/ETH/XMR wallet extraction
17. **CryptoBreaker** - ZIP password dictionary attack
18. **PCAPReconstructor** - Image reconstruction from traffic

## Test Coverage

Created `tests/test_predator_arsenale.py` with test classes for:

- `shannon_entropy` and `compute_file_hash` utilities
- `ThreatArtifact` dataclass
- `YaraEngine` (graceful degradation)
- `TLSFingerprint` (known/unknown JA3)
- `BehavioralML` (CPU/memory thresholds)
- `StegoHunter` (EOF detection, signatures)
- `VaultHunter` (hidden dirs, double extensions)
- `BulkExtractor` (email, URL, oversized files)
- `DatabaseForensics` (suspicious tables)
- `VideoAnalyzer` (format detection)
- `BlockchainAnalyzer` (ETH wallet extraction)
- `CryptoBreaker` (missing/unprotected ZIPs)
- `PredatorHunt` controller (init, artifact storage, error paths)

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt

# Standard analysis
python -m src.predator_arsenale /sdcard/Download

# With specific files
python -m src.predator_arsenale --apk app.apk --pcap capture.pcap /sdcard

# With root (more powerful)
su -c "python /data/data/com.termux/files/home/src/predator_arsenale.py /sdcard"

# Run tests
pytest tests/test_predator_arsenale.py -v
```
