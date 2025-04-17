# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added

### Changed
- Adapt Coordinate type to use WKBElement Geography [#287](https://github.com/ie3-institute/pypsdm/issues/287)

### Removed

### Fixed


## 0.0.5

### Changed
- Cleaned up dependencies [#299](https://github.com/ie3-institute/pypsdm/issues/299)

## 0.0.4

### Added

- Added `Transformers2WResult` dictionary support [#217](https://github.com/ie3-institute/pypsdm/pull/217)
- `PrimaryData` time series are now protected, introduced `add_time_series` method [#218](https://github.com/ie3-institute/pypsdm/pull/218)
- Added method to create nodes and lines [#223](https://github.com/ie3-institute/pypsdm/pull/223)
- Added graph traversal functionality [#224](https://github.com/ie3-institute/pypsdm/pull/224)
- Added method to create two winding transformer [#227](https://github.com/ie3-institute/pypsdm/pull/227)
- Allow execution with python 3.12 [#229](https://github.com/ie3-institute/pypsdm/issues/229) 
- Added ECDF plot example to plotting notebook [#263](https://github.com/ie3-institute/pypsdm/issues/263)

### Changed
- Add `s_ratedDC` to parameter for creation of `ElectricVehicles` [#236](https://github.com/ie3-institute/pypsdm/issues/236)
- Adapt to recent PSDM changes with regard to energy management systems [#164](https://github.com/ie3-institute/pypsdm/issue/164)
- Removed node from create method of energy management systems [#267](https://github.com/ie3-institute/pypsdm/issue/267)
- Changed default value for `cos_Phi` of create method of `ElectricVehicleChargingStations` to 1.0 [#272](https://github.com/ie3-institute/pypsdm/issue/272) 
- Fix `create_grid` notebook to PSDM changes with respect to Em [#281](https://github.com/ie3-institute/pypsdm/issues/281)

### Fixed
 - Fixed node identifier for plot of voltage over a branch [#240](https://github.com/ie3-institute/pypsdm/issue/240)
 - Fixed slack node identification if slack is not directly connected to a transformer [#238](https://github.com/ie3-institute/pypsdm/issue/238) 
 - Fixed dependabot tag [#261](https://github.com/ie3-institute/pypsdm/issues/261)
 - Fixed flex option results not being handled [#247](https://github.com/ie3-institute/pypsdm/issues/247)

## 0.0.3

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
