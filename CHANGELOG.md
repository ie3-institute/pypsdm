# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Subclasses of `Entities` support `__getitem__` with uuids, returning the associated series of the underlying `DataFrame` [#155](https://github.com/ie3-institute/pypsdm/pull/155)
- Support for initializing `LocalGwrDb` from environment variable [#155](https://github.com/ie3-institute/pypsdm/pull/155)
- ORM for accessing `ICON` weather data [#159](https://github.com/ie3-institute/pypsdm/pull/159)
- `LocalGwrDb` supports copying configs [#159](https://github.com/ie3-institute/pypsdm/pull/159)
- `Entities` support `__getitem__` with uuds [#159](https://github.com/ie3-institute/pypsdm/pull/159)
- Support for lines and transformer admittance matrix calculation [#161](https://github.com/ie3-institute/pypsdm/pull/161)
- `ExtendedNode(s)Result` are now calculated using the grids admittance matrix 
- Specific `Line(s)Result` and line utilisation calculation [[#176](https://github.com/ie3-institute/pypsdm/issues/176)]

### Changed
- Renamed `EnhancedNodeResult` and `EnhancedNodesResult` to `ExtendedNoderesult` and `ExtendedNodesresult` [#155](https://github.com/ie3-institute/pypsdm/pull/155)
- Data models from `pypsdm.models.*` can now be imported from the root module `pypsdm` [#159](https://github.com/ie3-institute/pypsdm/pull/159)
- All previous `ResultDict` and `ExtendedNodesResult` properties are now functions instead of properties

### Removed
-

### Fixed
- 
