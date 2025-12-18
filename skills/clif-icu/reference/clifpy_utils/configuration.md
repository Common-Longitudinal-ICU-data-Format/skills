# clifpy Configuration Reference

## clif_config.json Structure

Create a `clif_config.json` file in your project directory:

```json
{
  "data_directory": "/path/to/clif/tables",
  "filetype": "parquet",
  "timezone": "America/Chicago",
  "output_directory": "/path/to/output"
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `data_directory` | string | Path to directory containing CLIF table files (`clif_vitals.parquet`, etc.) |
| `filetype` | string | `"csv"` or `"parquet"` |
| `timezone` | string | Timezone string (e.g., `"UTC"`, `"America/New_York"`, `"US/Eastern"`) |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `output_directory` | string | `./output` | Where to save logs and validation results |

---

## Two Configuration Options

### Option 1: Config File (Recommended)

Create a `clif_config.json` file and let clifpy auto-detect it:

```python
from clifpy import ClifOrchestrator

# Auto-detect config.json in current directory
co = ClifOrchestrator()

# Or specify path explicitly
co = ClifOrchestrator(config_path="/path/to/clif_config.json")
```

**Advantages:**
- Reusable across scripts
- No hardcoded paths in code
- Easy to share configuration

### Option 2: Hardcoded Parameters

Pass configuration directly when initializing:

```python
from clifpy import ClifOrchestrator

co = ClifOrchestrator(
    data_directory="/path/to/data",
    filetype="parquet",
    timezone="America/Chicago",
    output_directory="./output"
)
```

**Use when:**
- Quick one-off analysis
- Parameters vary per script
- Testing different configurations

---

## Loading Priority

When both config file and parameters are provided:

1. **All required params provided directly** → use them (ignore config file)
2. **config_path provided** → load from that path, then params override config values
3. **No params and no config_path** → auto-detect `config.json` or `config.yaml` in current working directory

### Override Example

```python
# Load from config file but override timezone
co = ClifOrchestrator(
    config_path="clif_config.json",
    timezone="UTC"  # Overrides timezone from config file
)
```

---

## YAML Alternative

clifpy also supports YAML configuration files (`config.yaml` or `config.yml`):

```yaml
site: "YOUR_SITE_NAME"
tables_path: "/path/to/clif/tables"
filetype: "parquet"
timezone: "America/Chicago"
output_directory: "/path/to/output"
```

**Note:** In YAML, use `tables_path` instead of `data_directory`. clifpy automatically maps this field.

---

## Creating Config for Users

If a user doesn't have a config file, you can create one:

```python
from clifpy.utils.config import create_example_config

create_example_config(
    data_directory="/path/to/user/data",
    filetype="parquet",
    timezone="America/Chicago",
    output_directory="./output",
    config_path="./clif_config.json"
)
```

This creates a properly formatted JSON config file at the specified path.

---

## Related Documentation

| Topic | File |
|-------|------|
| Table class methods | [table_classes.md](table_classes.md) |
| ClifOrchestrator usage | [orchestrator.md](orchestrator.md) |
| Utility functions | [clifpy_functions.md](clifpy_functions.md) |
| Config loading code | [config.py](config.py) |
