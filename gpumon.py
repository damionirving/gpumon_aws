# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License").
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  or in the "license" file accompanying this file. This file is distributed
#  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#  express or implied. See the License for the specific language governing
#  permissions and limitations under the License.


# Key Modifications:

#  - Expanded Monitoring Scope.

#  - Improved Usability and Compatibility.
#  - Enhanced Reliability and Logging.


import argparse
import psutil
import urllib.request
import boto3
from pynvml import *
from datetime import datetime
from time import sleep, time
import logging


# Configure logging
logging.basicConfig(
    filename="/home/ubuntu/logs/gpumon.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Constants
BASE_URL = "http://169.254.169.254/latest/meta-data/"
INSTANCE_ID = urllib.request.urlopen(BASE_URL + "instance-id").read()
IMAGE_ID = urllib.request.urlopen(BASE_URL + "ami-id").read()
INSTANCE_TYPE = urllib.request.urlopen(BASE_URL + "instance-type").read()
INSTANCE_AZ = urllib.request.urlopen(BASE_URL + "placement/availability-zone").read()
EC2_REGION = INSTANCE_AZ[:-1]

# Decode if bytes
if isinstance(INSTANCE_ID, bytes):
    INSTANCE_ID = INSTANCE_ID.decode("utf-8").strip()

if isinstance(IMAGE_ID, bytes):
    IMAGE_ID = IMAGE_ID.decode("utf-8").strip()

if isinstance(INSTANCE_TYPE, bytes):
    INSTANCE_TYPE = INSTANCE_TYPE.decode("utf-8").strip()

if isinstance(EC2_REGION, bytes):
    EC2_REGION = EC2_REGION.decode("utf-8").strip()

logging.info(
    f"Decoded InstanceId type: {type(INSTANCE_ID)}, Image ID type: {type(IMAGE_ID)}, InstanceType type: {type(INSTANCE_TYPE)}"
)

# CloudWatch client
cloudwatch = boto3.client("cloudwatch", region_name=EC2_REGION)

# Flag for pushing metrics
PUSH_TO_CW = True

TMP_FILE = "/tmp/GPU_TEMP"
TIMESTAMP = datetime.now().strftime("%Y-%m-%dT%H")
TMP_FILE_SAVED = TMP_FILE + TIMESTAMP


def getPowerDraw(handle):
    """Retrieve the power draw of the GPU."""
    global PUSH_TO_CW
    try:
        powDraw = nvmlDeviceGetPowerUsage(handle) / 1000.0
        return f"{powDraw:.2f}"
    except NVMLError as err:
        logging.error(f"Error getting power draw: {handleError(err)}")
        PUSH_TO_CW = False
        return "0"


def getTemp(handle):
    """Retrieve the temperature of the GPU."""
    global PUSH_TO_CW
    try:
        return str(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU))
    except NVMLError as err:
        logging.error(f"Error getting temperature: {handleError(err)}")
        PUSH_TO_CW = False
        return "0"


def getUtilization(handle):
    """Retrieve the utilization rates of the GPU."""
    global PUSH_TO_CW
    try:
        util = nvmlDeviceGetUtilizationRates(handle)
        return util, str(util.gpu), str(util.memory)
    except NVMLError as err:
        logging.error(f"Error getting utilization: {handleError(err)}")
        PUSH_TO_CW = False
        return None, "0", "0"


def getCpuUtilization(interval):
    """Retrieve the CPU utilization as a percentage."""
    try:
        return psutil.cpu_percent(interval=interval)
    except Exception as e:
        logging.error(f"Error getting CPU utilization: {e}")
        return 0.0


def getEc2MemoryUsage():
    """Retrieve the EC2 memory usage as a percentage."""
    try:
        memory = psutil.virtual_memory()
        return memory.percent
    except Exception as e:
        logging.error(f"Error getting EC2 memory usage: {e}")
        return 0.0


def logResults(i, util, gpu_util, mem_util, powDrawStr, temp, cpu_util, ec2_mem_util):
    """Log results to a file and optionally send them to CloudWatch."""
    global PUSH_TO_CW
    try:
        # Log results to a temporary file
        with open(TMP_FILE_SAVED, "a+") as gpu_logs:
            writeString = f"{i},{gpu_util},{mem_util},{powDrawStr},{temp},{cpu_util},{ec2_mem_util}\n"
            gpu_logs.write(writeString)
    except Exception as e:
        logging.error(f"Error writing to file: {e}")

    if PUSH_TO_CW:
        MY_DIMENSIONS = [
            {"Name": "InstanceId", "Value": INSTANCE_ID},
            {"Name": "ImageId", "Value": IMAGE_ID},
            {"Name": "InstanceType", "Value": INSTANCE_TYPE},
            {"Name": "GPUNumber", "Value": str(i)},
        ]

        try:
            # Send metrics to CloudWatch
            cloudwatch.put_metric_data(
                MetricData=[
                    {
                        "MetricName": "GPU Usage",
                        "Dimensions": MY_DIMENSIONS,
                        "Unit": "Percent",
                        "StorageResolution": store_reso,
                        "Value": util.gpu,
                    },
                    {
                        "MetricName": "Memory Usage (GPU)",
                        "Dimensions": MY_DIMENSIONS,
                        "Unit": "Percent",
                        "StorageResolution": store_reso,
                        "Value": util.memory,
                    },
                    {
                        "MetricName": "Power Usage (Watts)",
                        "Dimensions": MY_DIMENSIONS,
                        "Unit": "None",
                        "StorageResolution": store_reso,
                        "Value": float(powDrawStr),
                    },
                    {
                        "MetricName": "Temperature (C)",
                        "Dimensions": MY_DIMENSIONS,
                        "Unit": "None",
                        "StorageResolution": store_reso,
                        "Value": int(temp),
                    },
                    {
                        "MetricName": "CPU Usage",
                        "Dimensions": MY_DIMENSIONS,
                        "Unit": "Percent",
                        "StorageResolution": store_reso,
                        "Value": cpu_util,
                    },
                    {
                        "MetricName": "Memory Usage (EC2)",
                        "Dimensions": MY_DIMENSIONS,
                        "Unit": "Percent",
                        "StorageResolution": store_reso,
                        "Value": ec2_mem_util,
                    },
                ],
                Namespace=my_NameSpace,
            )
        except Exception as e:
            logging.error(f"Error sending data to CloudWatch: {e}")


def main():
    global sleep_interval, store_reso, my_NameSpace

    parser = argparse.ArgumentParser(
        description="GPU, CPU, and Memory Monitoring Script"
    )
    parser.add_argument(
        "--sleep_interval",
        type=int,
        default=10,
        help="Time interval (in seconds) between each monitoring cycle (default: 10 seconds)",
    )
    parser.add_argument(
        "--store_reso",
        type=int,
        default=60,
        help="Storage resolution for CloudWatch metrics (default: 60 seconds)",
    )
    parser.add_argument(
        "--my_NameSpace",
        type=str,
        default="UsageMetrics",
        help="Namespace for CloudWatch metrics (default: UsageMetrics)",
    )

    args = parser.parse_args()
    sleep_interval = args.sleep_interval
    store_reso = args.store_reso
    my_NameSpace = args.my_NameSpace

    try:
        nvmlInit()
        deviceCount = nvmlDeviceGetCount()

        while True:
            global PUSH_TO_CW
            PUSH_TO_CW = True

            # Measure GPU metric collection time
            start_time = time()
            for i in range(deviceCount):
                handle = nvmlDeviceGetHandleByIndex(i)
                powDrawStr = getPowerDraw(handle)
                temp = getTemp(handle)
                util, gpu_util, mem_util = getUtilization(handle)
            end_time = time()

            gpu_collection_time = end_time - start_time
            logging.info(f"GPU Collection Time: {gpu_collection_time} seconds")

            # Adjust CPU interval based on GPU collection time
            cpu_interval = max(0.1, gpu_collection_time)
            cpu_util = getCpuUtilization(interval=cpu_interval)

            # Fetch EC2 memory usage
            ec2_mem_util = getEc2MemoryUsage()

            # Log results for all GPUs
            for i in range(deviceCount):
                handle = nvmlDeviceGetHandleByIndex(i)
                powDrawStr = getPowerDraw(handle)
                temp = getTemp(handle)
                util, gpu_util, mem_util = getUtilization(handle)
                logResults(
                    i,
                    util,
                    gpu_util,
                    mem_util,
                    powDrawStr,
                    temp,
                    cpu_util,
                    ec2_mem_util,
                )

            sleep(sleep_interval)
    finally:
        nvmlShutdown()


if __name__ == "__main__":
    main()
