# Changelog

## [Unreleased]

### Changed
- **Cleaner error logs when the IPBox is unreachable.** When the controller
  at `host:port` does not respond (e.g. it is powered off, disconnected
  from the network, or blocked by a firewall), Home Assistant now logs
  a single-line error such as `Error requesting ipbuilding data:
  Cannot connect to host 192.168.x.x:30200` instead of a multi-line
  Python traceback through the underlying HTTP client. The integration's
  behaviour is unchanged: the config entry still goes into retry mode
  with the same exponential backoff, and the existing
  `ConfigEntryNotReady` / `Retrying in N seconds` flow continues to
  work as before. After this change, `IPBuildingCannotConnect` also
  inherits from `aiohttp.ClientError` so that Home Assistant's standard
  transport-error handling picks it up automatically.

## [1.0.0] - 2026-06-13

First HACS-ready release of the IPBuilding integration. The 0.x line was
considered stable for daily use, but 1.0.0 marks the first version that
officially meets the Home Assistant Bronze quality scale and ships with the
metadata, CI and documentation expected of a HACS-default repository.

This release went through two release candidates (rc1, rc2) to land the
review findings non-destructively. The rc1 → 1.0.0 change set:

- The test-fixture contradiction in `tests/conftest.py` is fixed.
- The coordinator now removes vanished devices after two consecutive
  partial polls and conditionally skips polling when no polled-type
  device is present.
- `IPBuildingAPI.set_value` uses a separate write timeout
  (`write_timeout=3.0`) so a wedged controller fails fast on writes.
- The power sensor keeps `SensorStateClass.MEASUREMENT` because a
  real install wires it into `integration` helper sensors for the
  per-circuit kWh view in the Energy Dashboard; removing it would
  silently break those helpers. The estimate is documented in the
  sensor's docstring.
- See `1.0.0-rc2` below for the full rc1 → rc2 changelog.

### Fixed
- **Test fixture contradiction** (`tests/conftest.py`): `mock_setup_entry`
  is a no-op fixture. The previous version of this fixture (in the rc1
  review branch) patched the module-level `async_setup_entry` to
  `return_value=True`, which short-circuited the real entry setup —
  including the assignment of `entry.runtime_data`. The whole
  integration depends on that dataclass being set, so any test that
  wanted to assert the entry actually loaded had to do so against a
  fixture that contradicted the assertion. The replacement keeps
  `mock_setup_entry` as a no-op so the entry setup is exercised
  end-to-end (coordinator + runtime_data are created and platform
  wiring runs), which is what every test in this repo actually needs.
- **Coordinator device-removal regression** (`coordinator.py`): the
  removal-after-two-missed-polls logic now correctly tracks devices
  that were present in the initial snapshot. The previous
  implementation only tracked keys that had been seen in a partial
  poll, which meant devices that were present at setup but absent
  from the very first partial poll were never counted as missing.
  The set of "seen" keys is now seeded from `self._initial_data` so
  every device starts with a clean miss counter, and the device is
  dropped from the coordinator snapshot after two consecutive
  partial polls that don't include it.
- **Test for `set_value` call signature** (`tests/test_api.py`): the
  `test_set_value_default_action_type` test used `args[1]` to read
  the request params, but `IPBuildingAPI.set_value` calls
  `session.get(url, params=params)`, which makes `params` a keyword
  argument, not a second positional. The test now reads the params
  via `kwargs["params"]`, which is the actual call shape.
- **`pytest.ini` addopts duplicated the hass plugin** (`pytest.ini`):
  the previous `addopts = -p pytest_homeassistant_custom_component.plugins`
  caused `pytest` to crash with "Plugin already registered under a
  different name" because the plugin is also auto-registered via its
  `entry_points`. The `addopts` line has been removed; the plugin
  is loaded once via the standard mechanism and `pytest` now runs
  from the repository root with the simple `pytest` invocation
  documented in `DEVELOPMENT.md`.
- **Magic number for kind skip** (`switch.py`): the `Kind == 1` skip
  for relays that belong to the light platform is now spelled
  `Kind == KIND_LIGHT` using the named constant.
- **Duplicated `IPBuildingData` dataclass** (`__init__.py`,
  `type_aliases.py`): the definition now lives in one place
  (`type_aliases.py`) and is re-exported by `__init__.py`. Previously the
  two definitions could silently drift apart.
- **Dead `unique_id` assignment in entity base** (`entity.py`): the base
  no longer assigns a unique_id that every subclass immediately
  overwrites. The base class docstring now requires subclasses to set
  it themselves (the format is pinned by a regression test).
- **Entity names no longer duplicate the device name** (`entity.py`,
  `sensor.py`): the base `IPBuildingEntity` and the
  `IPBuildingSystemSensor` previously set ``_attr_name`` to the
  device description, which combined with the matching
  ``DeviceInfo.name`` produced duplicated entity_ids like
  ``light.kitchen_dimmer_kitchen_dimmer`` and friendly names like
  "Kitchen Dimmer Kitchen Dimmer". With ``has_entity_name = True``
  the right pattern is to leave ``_attr_name = None`` (so the entity
  inherits the device name) or, for sub-entities, set ``_attr_name``
  to a short distinct suffix. The base class now declares
  ``_attr_name: str | None = None``; the system-sensor subclass
  relies on that; the power-sensor subclass sets ``_attr_name =
  "Power"`` to produce ``sensor.kitchen_dimmer_power`` instead of
  ``sensor.kitchen_dimmer_kitchen_dimmer_power``.

### Changed
- **Coordinator polling is now conditional** (`coordinator.py`): when
  the initial device snapshot contains no device of a polled type
  (RELAY, DIMMER, DMX, LED), the update interval is set to `None` and
  the controller is only refreshed when an entity triggers
  `async_request_refresh`. Installations that only have buttons,
  sensors or scenes no longer generate a wasted partial poll every
  20 seconds.
- **Coordinator removes vanished devices** (`coordinator.py`): if a
  device that was present in the previous partial poll is missing from
  the next one, it is only dropped from the coordinator snapshot after
  two consecutive missed polls. This protects against transient network
  blips while still letting entities eventually disappear when their
  device is removed on the controller. Existing entities are
  unaffected; removal only kicks in after the first poll cycle.
- **Sensor "system" hub lookup is centralised** (`sensor.py`): the
  time/regime sensors now look up their hub id from `HUB_BY_TYPE`
  instead of hard-coding the string `"hub_system"` in two places.
- **`IPBuildingAPI.set_value` uses a separate write timeout** (`api.py`):
  the constructor takes a `write_timeout` (default 3.0 s) used by
  `set_value`; the read timeout (default 10.0 s) is unchanged. The
  default is non-breaking for existing callers.

### Added
- **MIT LICENSE file** at the repository root; `hacs.json` declares
  `"license": "MIT"`.
- **Security notes section in the README** documenting that the
  IPBox has no authentication, the API is unencrypted HTTP, and
  state-changing actions are HTTP GET requests (the IPBox firmware
  only accepts GET on `/action/action`; POST returns
  `405 Method Not Allowed` with `Allow: GET`).
- **`.gitignore` entries for `venv/`, `.venv/` and `**/__pycache__/`**.
- **New tests**: `test_api.py`, `test_coordinator.py`, `test_switch.py`,
  `test_button.py`, `test_sensor.py`, `test_scene.py`, `test_entity.py`
  and four new fixtures in `conftest.py`. The coordinator tests cover
  conditional polling, partial merging, removal-after-two-missed-polls
  and the error path. The API tests cover the type filter, response
  shape unwrapping, timeouts, the `set_value` action_type default, the
  write-timeout split and `validate_connection`. The full suite
  (`pytest` from the repository root) runs 38 tests and passes in well
  under a second on the bundled venv.

  The `tests/conftest.py` also adds an autouse wrapper around the
  upstream `enable_custom integrations` fixture from
  `pytest-homeassistant-custom-component`, so every test gets the
  custom-component loader for free without having to declare it as
  a parameter.

### Known limitations (considered but not implemented to avoid breaking changes)
- The IPBox REST API does not support HTTPS. Adding an HTTPS toggle in
  the config flow is on hold until the controller firmware supports it.
- The IPBox firmware only accepts HTTP `GET` for state-changing
  actions; the integration cannot switch to `POST` without a controller
  firmware change. A live check against `192.168.0.185` confirmed
  `405 Method Not Allowed` for both form-urlencoded and JSON POST
  bodies.
- `HUB_BY_TYPE` still registers hub devices for types that have no
  platform implementation (DMX, LED, energy, temperature, weather,
  access, KMI). Pruning them would orphan device-registry entries on
  existing installs. New platforms will be added in a future release.
- The integration still calls `coordinator.async_request_refresh()`
  after every `light.turn_on/off` and `switch.turn_on/off`. Removing
  these would introduce up to a 20 s feedback delay on toggles. The
  current behaviour is preserved.
- The coordinator's `IPBuildingEntity.available` property still relies
  on the controller's `Visible` field; devices that disappear from the
  controller are now removed from the coordinator snapshot (after
  two missed polls), but their previously-registered entity is not
  removed from Home Assistant's entity registry.
- **Power sensor keeps `SensorStateClass.MEASUREMENT` despite the value
  being an estimate.** The 1.0.0 code review flagged that the
  estimated wattage (rated `Watt` × dimmer percentage, or `Watt` when
  a relay is on) should not be treated as a real meter by Home
  Assistant's Energy Dashboard. We considered removing
  `MEASUREMENT`, but a live inspection of a real install showed that
  the power sensors are wired as the source of `integration` helper
  sensors (e.g. `sensor.verlichting_woonkamer_energy`,
  `sensor.verlichting_bureau_energy`,
  `sensor.traphal_verlichting_energy`,
  `sensor.badkamer_verlichting_energy`) that drive the user's
  Energy Dashboard for individual light circuits. Removing
  `MEASUREMENT` would silently break those setups. The estimate is
  documented in the sensor's docstring ("estimate, not measurement")
  and the sensor remains hidden by default; users who care about
  absolute accuracy should add a real meter (Shelly EM, P1, etc.) and
  stop using the IPBuilding power sensor for billing or energy
  statistics.

## [1.0.0-rc2] - 2026-06-13

Second release candidate of 1.0.0. Addresses findings from the rc1
code review. **No breaking changes** versus rc1: existing config
entries, entities, hub devices and toggle behaviour are preserved.
Where the review recommended a change, this rc either implements it
non-destructively or documents the limitation explicitly.

### Notes for existing users
- The repository has been transferred from `Sonic-Rocket/HA-IPBuilding` to
  `markminnoye/HA-IPBuilding`. GitHub redirects the old URL automatically,
  so existing HACS installs continue to receive updates without any action
  on your part. If you prefer, you can remove the old custom repository
  from HACS and re-add the new URL, but this is purely cosmetic.

## [0.4.1] - 2026-06-13

### Fixed
- **Duplicate entities on upgrade**: 0.3.0/0.4.0 included the config-entry
  id in every entity `unique_id` (`ipbuilding_{entry_id}_{type}_{id}`), which
  changed the unique_id of every existing entity on upgrade and caused Home
  Assistant to register all entities a second time. The `entry_id` prefix has
  been removed; unique_ids are back to the stable `ipbuilding_{type}_{id}`
  format. The config flow still enforces one config entry per `host:port`, so
  the prefix was redundant.

### Tests
- New regression test `test_entity_unique_id_format` pins the
  `ipbuilding_{type}_{id}` format and asserts that no entity `unique_id`
  contains the config-entry id.

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
