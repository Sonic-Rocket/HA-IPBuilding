# Changelog

## [0.4.0] - 2026-06-12

### Added
- **Scene platform**: support for IPBuilding spheres (Type 100) and
  temp-spheres (Type 101); scenes can be activated from Home Assistant.
  Devices are grouped under a new `hub_scenes` hub identifier.
- **State visibility control**:
  - Button entities use `_attr_entity_registry_visible_default = False`
  - Power sensors (created from the `Watt` attribute) hide state by default
  - Entities stay fully functional; they just don't clutter dashboards
- **Visible property support**: every platform (button, sensor, switch,
  light, scene) exposes an `available` property that mirrors the `Visible`
  field of the IPBuilding API response; devices with `"Visible": false`
  are reported as `unavailable` in HA.

### Improved
- Consistent `available` property across all platform classes.
- Power-sensor hub selection uses the `HUB_BY_TYPE` constant.

## [0.3.0] - 2026-06-07

### Added
- **Bronze quality scale**: `manifest.json` now declares
  `quality_scale: bronze`, a non-empty `codeowners`, an `issue_tracker` URL and
  `integration_type: hub`.
- **Translations**: `translations/en.json` and `translations/nl.json` with
  the user-facing strings for the config flow and its error/abort reasons.
- **Tests**: a `tests/` suite (`test_init.py`, `test_config_flow.py`,
  `test_light.py`) that uses `pytest-homeassistant-custom-component` and
  mocks the `IPBuildingAPI`. Wired up via `pytest.ini` and
  `requirements_dev.txt`.
- **Typed runtime data**: a `IPBuildingData` dataclass exposed as
  `entry.runtime_data` and accessed by every platform through the typed
  `IPBuildingConfigEntry` alias declared in `type_aliases.py`.
- **`IPBuildingDataCoordinator`**: a `DataUpdateCoordinator[dict]` subclass
  with `config_entry` bound, an initial full snapshot in `_async_setup`,
  and a merge-based `_async_update_data` that never mutates existing
  coordinator state in place.
- **`IPBuildingEntity`**: a shared `CoordinatorEntity` base in
  `entity.py` that owns the `unique_id`, `device_info`, `_device_data`
  cache and `available` property.
- **API hardening**: `IPBuildingAPI` now exposes `validate_connection()`,
  uses `asyncio.timeout` instead of the third-party `async_timeout`
  package, and raises typed `IPBuildingCannotConnect` /
  `IPBuildingInvalidResponse` exceptions.

### Changed
- **`config_flow.py`**: rewritten to use `ConfigFlowResult`, validate the
  connection against the live controller and set a stable
  `host:port`-based `unique_id` with `async_set_unique_id` +
  `_abort_if_unique_id_configured`.
- **`__init__.py`**: uses `entry.runtime_data`, raises
  `ConfigEntryNotReady` on connectivity failures (replacing the
  `return False` pattern), and groups hub devices via the new
  `HUB_BY_TYPE` constant.
- **Optimistic updates removed**: light and switch platforms now call
  `coordinator.async_request_refresh()` after a write instead of
  mutating `coordinator.data` directly, so the next refresh produces a
  fresh dict and the entity state stays in sync.
- **Light platform**: split into `IPBuildingBrightnessLight` and
  `IPBuildingOnOffLight` so `color_mode` and `supported_color_modes` are
  set on the class level.
- **Switch platform**: uses `SwitchDeviceClass` enum and a Kind-based
  mapping for device class / icon; the brittle "smoke" string-match is
  gone.
- **Sensor platform**: explicit type-narrowing via `_to_int()` and
  `SensorDeviceClass.POWER` enum; power-sensor hub selection uses
  `HUB_BY_TYPE`.
- **Scene platform**: reuses the coordinator snapshot and reports API
  failures as warnings instead of letting them bubble up.

### Removed
- Direct `self.coordinator.data[...] = ...` mutations from
  `light.py`/`switch.py`.
- `update_method=` based coordinator construction in favour of a
  `_async_update_data` override.
