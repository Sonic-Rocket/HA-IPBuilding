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

## Requirements

- A working IPBuilding installation with an **IPBox** controller
- Network access from your Home Assistant instance to the IPBox
- API/controller access on the IPBox (IP address/hostname, port and credentials, depending on your setup)
- Home Assistant 2024.x or newer 

## Installation

### HACS (recommended)
[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=markminnoye&repository=HA-IPBuilding&category=integration)
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

Configuration is done via the UI, or manually by editing `configuration.yaml`.

Basic example:

```yaml
ipbuilding:
  host: 192.168.1.50
  port: 12345
  username: "ha_integration"
  password: "your-password"
  # Optional filters / mappings
  include_lights: true
  include_switches: true
  include_scenes: true
  include_ventilation: true
