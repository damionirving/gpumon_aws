Here is the modified version of your content with the hyperlink included:

---

# GPU Monitoring Script (`gpumon.py`)

## Overview

This repository contains an enhanced version of `gpumon.py`, a Python script for monitoring GPU utilization, power draw, temperature, and additional system metrics (CPU and memory usage). The script is designed to log metrics locally and push them to AWS CloudWatch, providing a centralized view of system performance.

The updated version introduces several new features and improvements over the original script, making it more robust, flexible, and capable of monitoring both GPU and system-level metrics. For more details, refer to the [AWS source](https://aws.amazon.com/blogs/machine-learning/monitoring-gpu-utilization-with-amazon-cloudwatch/?source=post_page-----a5789088cf74--------------------------------).

---

## Key Changes and Benefits

### 1. **Logging Integration**
- **Change**: Added the `logging` module to capture runtime details, errors, and debug information.
- **Benefit**: Provides a structured and persistent way to monitor script behavior and troubleshoot issues.

### 2. **Command-line Argument Parsing**
- **Change**: Introduced `argparse` to configure runtime parameters (e.g., `--sleep_interval`, `--store_reso`, `--my_NameSpace`).
- **Benefit**: Allows for flexible configuration without modifying the code, supporting different environments and use cases.

### 3. **CPU and EC2 Memory Monitoring**
- **Change**: Added functions to monitor CPU utilization and EC2 memory usage using `psutil`.
- **Benefit**: Provides a comprehensive view of system performance, including both GPU and system-level metrics.

### 4. **Enhanced Error Handling**
- **Change**: Improved error handling with better logging and fallback values for GPU metrics.
- **Benefit**: Ensures resilience and prevents crashes due to unexpected errors.

### 5. **Explicit Metadata Decoding**
- **Change**: Decoded instance metadata (e.g., `INSTANCE_ID`, `IMAGE_ID`) to ensure compatibility with Python 3.
- **Benefit**: Avoids runtime errors related to data types.

### 6. **Measurement of GPU Metric Collection Time**
- **Change**: Measured GPU metric collection time and used it to adjust CPU monitoring intervals dynamically.
- **Benefit**: Optimizes resource usage and ensures accurate CPU utilization metrics.

### 7. **CloudWatch Metric Enhancements**
- **Change**: Added `CPU Usage` and `Memory Usage (EC2)` as new metrics to CloudWatch.
- **Benefit**: Enables centralized monitoring of GPU, CPU, and memory metrics in one dashboard.

### 8. **Improved File Handling**
- **Change**: Used `with open` for file operations.
- **Benefit**: Ensures proper resource management and reduces the risk of file descriptor leaks.

### 9. **Python 3 Compatibility**
- **Change**: Replaced `urllib2` with `urllib.request` for metadata fetching.
- **Benefit**: Ensures compatibility with modern Python environments.

---

## Usage Instructions

### Example Command
Run the script with the following command:

```bash
python gpumon.py --sleep_interval 10 --store_reso 60 --my_NameSpace UsageMetrics
```

### Command-line Arguments
| Argument            | Description                                    | Default Value         |
|---------------------|------------------------------------------------|-----------------------|
| `--sleep_interval`  | Time (in seconds) between monitoring cycles.  | `10`                 |
| `--store_reso`      | CloudWatch storage resolution (1-60 seconds). | `60`                 |
| `--my_NameSpace`    | CloudWatch namespace for metrics.             | `UsageMetrics`       |

### Example Output
Metrics collected:
- GPU Utilization (%).
- Memory Utilization (GPU) (%).
- Power Usage (Watts).
- Temperature (°C).
- CPU Utilization (%).
- Memory Usage (EC2) (%).

Sample log file output (`/home/ubuntu/logs/gpumon.log`):
```
2025-01-15 12:34:56 - INFO - GPU Collection Time: 0.123 seconds
2025-01-15 12:34:56 - INFO - Decoded InstanceId type: <class 'str'>, Image ID type: <class 'str'>, InstanceType type: <class 'str'>
```

---

## Example Code Usage

### Fetching GPU Metrics
```python
from pynvml import *

nvmlInit()
deviceCount = nvmlDeviceGetCount()

for i in range(deviceCount):
    handle = nvmlDeviceGetHandleByIndex(i)
    power_draw = nvmlDeviceGetPowerUsage(handle) / 1000.0
    temperature = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
    utilization = nvmlDeviceGetUtilizationRates(handle)
    print(f"GPU {i}: Power={power_draw}W, Temp={temperature}°C, Util={utilization.gpu}%")

nvmlShutdown()
```

### Fetching CPU and EC2 Memory Metrics
```python
import psutil

cpu_util = psutil.cpu_percent(interval=1)
ec2_memory = psutil.virtual_memory().percent
print(f"CPU Usage: {cpu_util}%, EC2 Memory Usage: {ec2_memory}%")
```

---

## License
This script is licensed under the Apache License, Version 2.0. See the [LICENSE](https://github.com/apache/.github/blob/main/LICENSE) file for details.