# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Added `Transformers2WResult` dictionary support [#217](https://github.com/ie3-institute/pypsdm/pull/217)
- `PrimaryData` time series are now protected, introduced `add_time_series` method [#218](https://github.com/ie3-institute/pypsdm/pull/218)
- Added method to create nodes and lines [#223](https://github.com/ie3-institute/pypsdm/pull/223)
- Added graph traversal functionality [#224](https://github.com/ie3-institute/pypsdm/pull/224)
- Added method to create two winding transformer [#227](https://github.com/ie3-institute/pypsdm/pull/227)

### Changed

### Removed

### Fixed

## [0.0.3]

### Added

- Subclasses of `Entities` support `__getitem__` with uuids, returning the associated series of the underlying `DataFrame` [#155](https://github.com/ie3-institute/pypsdm/pull/155)
- Support for initializing `LocalGwrDb` from environment variable [#155](https://github.com/ie3-institute/pypsdm/pull/155)
- ORM for accessing `ICON` weather data [#159](https://github.com/ie3-institute/pypsdm/pull/159)
- `LocalGwrDb` supports copying configs [#159](https://github.com/ie3-institute/pypsdm/pull/159)
- `Entities` support `__getitem__` with uuds [#159](https://github.com/ie3-institute/pypsdm/pull/159)
- Support for lines and transformer admittance matrix calculation [#161](https://github.com/ie3-institute/pypsdm/pull/161)
- `ExtendedNode(s)Result` are now calculated using the grids admittance matrix
- Specific `Line(s)Result` and line utilisation calculation [#176](https://github.com/ie3-institute/pypsdm/issues/176)
- Big refactoring of result types to extract more generic time series [#192](https://github.com/ie3-institute/pypsdm/pull/192)
- Result types do not contain uuid and optional name anymore, but time series dicts now have Entity key that contain the information [#192](https://github.com/ie3-institute/pypsdm/pull/192)
- Add WeatherDict data types and retrieval of weighted nodal weather [#193](https://github.com/ie3-institute/pypsdm/issues/193)

### Changed

- Renamed `EnhancedNodeResult` and `EnhancedNodesResult` to `ExtendedNoderesult` and `ExtendedNodesresult` [#155](https://github.com/ie3-institute/pypsdm/pull/155)
- Data models from `pypsdm.models.*` can now be imported from the root module `pypsdm` [#159](https://github.com/ie3-institute/pypsdm/pull/159)
- All previous `ResultDict` and `ExtendedNodesResult` properties are now functions instead of properties

### Removed

-

### Fixed

-
