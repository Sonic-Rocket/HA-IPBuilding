# Home Assistant Integration for IPBuilding

Control your **IPBuilding** smart living system directly from Home Assistant — no extra apps or cloud services required.

This integration lets you control lights, scenes, ventilation, zone heating and other building automation features from a single interface.

## How it works

This integration communicates with the **IPBox** via its built-in REST API. The IPBox is the central controller of your IPBuilding installation and acts as the single point of communication. Other IPBuilding hardware — such as switch modules, dimmers or sensors — is not accessed directly; all commands are routed through the IPBox.

> **Requirement:** You need an IPBox reachable on your local network, with its REST API enabled.
## Features

- Discover and control IPBuilding **lights** and **switches**
- Trigger IPBuilding **scenes / sferen** from Home Assistant
- Control **ventilation** modes and other climate-related functions
- Map IPBuilding entities to Home Assistant entities for dashboards and automations
- Designed for both residential and assisted-living / workspace deployments

This integration creates the following Home Assistant platforms: `light`, `switch`, `button`, `sensor`, and `scene`. ## Requirements {#prerequisites} - A working IPBuilding installation with an **IPBox** controller - Network access from your Home Assistant instance to the IPBox - API/controller access on the IPBox (IP address/hostname, port and credentials, depending on your setup) - Home Assistant 2024.x or newer ## Installation
### HACS (recommended)

Make sure the [prerequisites](#prerequisites) are met before installing.

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=markminnoye&repository=HA-IPBuilding&category=integration)
[![Version](https://img.shields.io/github/v/release/markminnoye/HA-IPBuilding)](https://github.com/markminnoye/HA-IPBuilding/releases/latest)
[![License](https://img.shields.io/github/license/markminnoye/HA-IPBuilding)](LICENSE)
[![Quality Scale](https://img.shields.io/badge/quality%20scale-bronze-brightgreen)](https://developers.home-assistant.io/docs/core/integration-quality-scale/)
1. Add this repository as a **Custom repository** in HACS. 
2. Search for **HA-IPBuilding** in HACS.
3. Install the integration and **restart Home Assistant**.

### Manual installation

1. Copy the `custom_components/ipbuilding` directory from this repository  
   into your Home Assistant `config/custom_components` folder.

   Final path:

   - `config/custom_components/ipbuilding`

2. Restart Home Assistant.

## Configuration

The integration is configured entirely through the Home Assistant user interface — no YAML is required.

1. Make sure your **IPBox** is reachable on the local network and its REST API is enabled (default port: `30200`).
2. In Home Assistant, go to **Settings → Devices & Services → Add Integration**.
3. Search for **IPBuilding** and follow the prompts.
4. You will be asked for:
   - **Host**: the IP address or hostname of your IPBox (e.g. `192.168.1.50`)
   - **Port**: the REST API port (default `30200`)

The config flow validates the connection before saving, and only one config entry per `host:port` is allowed.

## Actions

The integration does not register custom service actions. All functionality is exposed through standard Home Assistant service calls available on the created entities:

- `light.turn_on` / `light.turn_off` — controls relays, dimmers, DMX and LED devices
- `switch.turn_on` / `switch.turn_off` — controls switches and ventilation units
- `button.press` — triggers IPBuilding buttons (momentary actions)
- `scene.turn_on` — activates IPBuilding spheres / sferen (Type 100 and 101)
- `homeassistant.update_entity` — forces an immediate refresh of an entity's state

## Removing the integration

To remove the integration, go to **Settings → Devices & Services → IPBuilding**, select your entry and click **Delete**. This only removes the integration from Home Assistant — no changes are made to the IPBox or its configuration.

## Issues and feature requests

Please use the [issue tracker](https://github.com/markminnoye/HA-IPBuilding/issues) to report bugs or request features. When reporting a bug, include:

- Home Assistant version
- Integration version (see **Settings → Devices & Services → IPBuilding**)
- Relevant log output from **Settings → System → Logs** (filter on `ipbuilding`)
- A description of your IPBox setup (firmware version, device types involved)

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.