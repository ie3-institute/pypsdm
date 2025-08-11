# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment Setup

**Poetry Environment Activation:**
```bash
source $(poetry env info --path)/bin/activate
```

**Install Dependencies:**
```bash
poetry install
```

## Common Development Commands

**Code Quality:**
```bash
# Format code with black
source $(poetry env info --path)/bin/activate && black .

# Run linter
source $(poetry env info --path)/bin/activate && flake8 .

# Run all pre-commit hooks
pre-commit run --all-files
```

**Testing:**
```bash
# Run all tests
source $(poetry env info --path)/bin/activate && python -m pytest

# Run specific test file
source $(poetry env info --path)/bin/activate && python -m pytest tests/path/to/test_file.py

# Run tests with specific pattern
source $(poetry env info --path)/bin/activate && python -m pytest -k "test_pattern"
```

**Dependency Management:**
```bash
# Check for unused dependencies
source $(poetry env info --path)/bin/activate && deptry .
```

## Code Architecture

**Core Components:**

1. **Models Package** (`pypsdm/models/`):
   - `input/`: Input data models for grid components and participants
   - `result/`: Result data models for simulation outputs
   - `ts/`: Time series data types and utilities
   - `gwr.py`: Main `GridWithResults` class combining input and result data

2. **Key Classes:**
   - `GridWithResults`: Main facade combining grid model and simulation results
   - `GridContainer`: Contains raw grid elements and system participants
   - `GridResultContainer`: Contains simulation results for grid and participants
   - `SystemParticipantsContainer`: Manages participants (loads, PVs, storage, etc.)

3. **Data Flow:**
   - CSV files → Container classes → Analysis/Plotting
   - Input models define grid structure and participant parameters
   - Result models contain time series simulation outputs
   - GridWithResults provides unified interface for analysis

**Supported Grid Elements:**
- Nodes, lines, transformers, switches
- Participants: loads, PVs, storage, EVs, heat pumps, biomass plants, wind energy converters
- Time series data with complex power values

**Key Features:**
- CSV-based data I/O with configurable delimiters
- Plotting utilities for grid visualization and result analysis
- Pandapower conversion capabilities
- Database integration for weather and geographic data
- Numba-optimized processing for performance

## Code Style Configuration

- **Black**: Line length 88 characters
- **Flake8**: Configured in `setup.cfg` with ignore rules for E203, E501, W503
- **isort**: Black-compatible profile
- **Pre-commit hooks**: black, flake8, isort

## Testing Structure

- Test resources located in `tests/resources/`
- Fixtures defined in `tests/conftest.py` for common test data paths
- Test data includes SimBench grids and VN_SIMONA results
- Tests organized by module structure matching `pypsdm/`

## Development Notes

- Uses Poetry for dependency management
- Python 3.11+ required
- Dataclasses with frozen=True for immutable data structures
- Type hints throughout codebase
- Loguru for logging
- Supports both input-only and input+results workflows