from pathlib import Path

import platform
import cpuinfo
import psutil


def collect_environment_description():
    cpu_info = cpuinfo.get_cpu_info()

    return {
        "machine": platform.node(),
        "os": platform.platform(),
        "cpu": "{} {} {}.{}.{}".format(
            cpu_info["vendor_id"],
            cpu_info["brand"],
            cpu_info["family"],
            cpu_info["model"],
            cpu_info["stepping"],
        ),
        "cores": "{} x {}".format(
            psutil.cpu_count(logical=False),
            psutil.cpu_count(logical=True) // psutil.cpu_count(logical=False),
        ),
        "memory": "{:.2f}GiB".format(psutil.virtual_memory().free / (2 ** 30)),
        "storage": "{:.2f}GiB".format(
            psutil.disk_usage(str(Path().absolute())).free / (2 ** 30)
        ),
    }
