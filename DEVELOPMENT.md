# Local Development

This project uses a Python virtual environment for local development to test the `ipbuilding` custom component.

## Prerequisites

- Python 3.14 or higher installed (the project now uses Python 3.14).
- The virtual environment is created in the `venv` directory.

## Setup

1. **Run the setup script:**

   ```bash
   ./setup_local_ha.sh
   ```

   This creates (or recreates) the `venv` virtual environment, installs Home Assistant, and links the custom component.

2. **Start Home Assistant:**

   ```bash
   ./venv/bin/hass -c config
   ```

   Or activate the venv first:

   ```bash
   source venv/bin/activate
   hass -c config
   ```

3. **Access Home Assistant:**

   Open your browser and navigate to: [http://localhost:8123](http://localhost:8123)

   You will need to go through the initial Home Assistant onboarding process (create a user, etc.). This data is stored in the `config` directory and will persist between restarts.

4. **Add the Integration:**

   - Go to **Settings** -> **Devices & Services**.
   - Click **Add Integration**.
   - Search for **IPBuilding**.
   - Follow the configuration steps.

## Rebuilding

Since the component is symlinked, changes to the Python files should be picked up after restarting Home Assistant.

To restart, press `Ctrl+C` in the terminal to stop the process, then run `./venv/bin/hass -c config` again.

## Running tests

The test suite uses `pytest-homeassistant-custom-component`. Install the
development requirements and run pytest from the repository root:

```bash
source venv/bin/activate
pip install -r requirements_dev.txt
pytest
```

Tests mock the `IPBuildingAPI` so no real controller is required.
