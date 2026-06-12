# IPBuilding Custom Component

## Overview

This Home Assistant custom component provides integration with the IPBuilding system. It allows you to control dimmers, retrieve sensor data, and trigger custom actions via the IPBuilding REST API.

## Quality scale

This integration targets the **bronze** tier of the Home Assistant integration
quality scale. It therefore:

- Configures entirely through the UI (config flow) with connection validation
- Sets a stable `unique_id` (`host:port`) and aborts duplicate entries
- Stores runtime data on `entry.runtime_data` via a typed `IPBuildingData` dataclass
- Uses a `DataUpdateCoordinator` subclass (`IPBuildingDataCoordinator`) with
  `config_entry` properly bound
- Raises `ConfigEntryNotReady` on connectivity failures so HA retries with back-off
- Catches specific exceptions (`IPBuildingCannotConnect`,
  `IPBuildingInvalidResponse`, `aiohttp.ClientError`) instead of generic `Exception`
- Imports `ConfigFlowResult` (not the deprecated `FlowResult`)
- Provides English (`translations/en.json`) and Dutch (`translations/nl.json`)
  translations
- Has a unit-test suite under `tests/`

## Supported Platforms

The integration automatically discovers and creates entities for the following IPBuilding device types:

- **Lights**: Dimmers (Type 2) and Relays with Kind=1 (Type 1)
- **Switches**: Relays (Type 1) with Kind≠1 (outlets, locks, fans, valves, etc.)
- **Sensors**:
  - Time sensors (Type 56)
  - Regime sensors (Type 200)
  - Power sensors (automatically created for devices with `Watt` attribute)
- **Buttons**: Button devices (Type 50)
- **Scenes**: Sphere (Type 100) and TempSphere (Type 101) devices

## API documentation

- **REST v1** (used by this integration): see [Important API Endpoints](#important-api-endpoints) below.
- **Legacy mobile API** (`/mobile/core/actions.php`): archived reference and analysis in [`docs/mobile-api.md`](../../docs/mobile-api.md) and [`docs/reference/actions.php`](../../docs/reference/actions.php).

## Important API Endpoints

### Dimmer Control

- **Endpoint**: `GET http://192.168.0.185:30200/api/v1/action/action?id=571&actionType=DIM&value=10`
- **Description**: Sets the dimmer with ID `571` to a value of `10` (range depends on your device).

### Other Useful Endpoints

- **Send an Action**: https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/6uctjo4/send-an-action
- **Client Command**: https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/mgu7sxs/client-commando
- **Temperature Deviation**: https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/51zmehz/temperature-deviation
- **Trigger Custom Item Action**: https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/h59aed0/trigger-customitem-action
- **Get Version**: https://www.postman.com/soft-techbv/ipbrestapi-s-public-workspace/request/2ygfarm/get-version

These links point to the official Postman documentation for the IPBuilding REST API and provide detailed request/response examples.

## Usage in Home Assistant

The component exposes services that wrap these API calls. Refer to the component's `services.yaml` (if present) or the code in `api.py` for the exact service names and parameters.

### Entity Features

#### State Visibility
For a cleaner UI, certain entity types have their state display hidden by default:
- **Buttons**: All button entities have state display disabled (`entity_registry_visible_default = False`)
- **Power Sensors**: Energy/power sensors created from the `Watt` attribute also hide state display by default

These entities remain functional but don't clutter the dashboard with unnecessary state information.

#### Visible Property
The integration respects the `Visible` property from the IPBuilding API. Entities with `"Visible": false` will be marked as unavailable in Home Assistant.

#### Power Monitoring
The component automatically creates power sensor entities for any Relay or Dimmer device that has a `Watt` attribute. These sensors:
- Use the `sensor` device class for power measurement
- Report power in Watts (W)
- Can be used in Home Assistant's Energy Dashboard
- Are linked to the same device group as their parent entity

#### Device Grouping
All entities are automatically grouped by their IPBuilding `Group` property:
- Each entity is linked to a device based on `Group.ID` and `Group.Name`
- This allows you to organize entities by room/area in Home Assistant
- The device manufacturer is set to "IPBuilding"

#### Entity Attributes
All entities expose the following IPBuilding properties as attributes:
- `IpAddress`: IP address of the physical device
- `Port`: Port number
- `Protocol`: Communication protocol
- `ID`: IPBuilding device ID
- `Status`: Current device status
- `Output`: Output configuration
- `Kind`: Device kind/subtype (see Kinds table below)

## Development

For local development, see the top-level `DEVELOPMENT.md` which contains instructions on setting up a virtual environment and running Home Assistant locally.

## API Documentation

### Postman Collection
A fork of the original Postman collection is available here:
https://web.postman.co/workspace/baebca0c-0802-4854-833a-7eb222d1a9b7/collection/1366031-733ffb24-a5bd-4883-a3cb-8a04fbc7e7a2

### Types

| Type | Object          |
| ---- | --------------- |
| 1    | Relais          |
| 2    | Dimmer          |
| 3    | Dmx             |
| 40   | EnergyCounter   |
| 41   | EnergyMeter     |
| 50   | Button          |
| 51   | Temperature     |
| 52   | Detector        |
| 53   | Analog sensor   |
| 54   | KMI             |
| 55   | Weather station |
| 56   | Time of system  |
| 60   | Led             |
| 70   | AccessReader    |
| 80   | AccessKey       |
| 100  | Sphere          |
| 101  | TempSphere      |
| 102  | Prog            |
| 103  | AccessControl   |
| 150  | Script          |
| 200  | Regime          |

### Kinds

The `Kind` property determines the specific subtype of a device:

| Type | Object              |
| ---- | ------------------- |
| 1    | Licht               |
| 2    | Stopkontakt         |
| 3    | Automatisering      |
| 4    | Slot                |
| 5    | Ventilator          |
| 6    | Klep                |
| 7    | Temperatuur         |
| 8    | Niet van toepassing |


### Example Device Object

```json
{
    "__type": "Relais:IPBuilding",
    "ID": 547,
    "Type": 1,
    "Kind": 1,
    "Description": "Keuken LED [30.1.1]",
    "Group": {
        "ID": 4,
        "Name": "Keuken"
    },
    "IpAddress": "10.10.1.30",
    "Port": 1001,
    "Protocol": 0,
    "Visible": true,
    "MobileIcon": 0,
    "MobileVisible": true,
    "Output": 0,
    "Status": 0,
    "Watt": 0
}
```
