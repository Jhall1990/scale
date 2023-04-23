import os
import sys
import time
import yaml
import argparse
from HX711 import SimpleHX711, Mass


class Config():
    def __init__(self):
        self.dt_pin = None
        self.sck_pin = None
        self.samples = None
        self.ref_unit = None
        self.offset = None
        self.min_weight = None
        self.max_weight = None

    @staticmethod
    def from_yaml(path):
        cfg = Config()
        with open(path, "r", encoding="utf-8") as config:
            config_dict = yaml.safe_load(config)

        try:
            cfg.dt_pin = config_dict["DT_PIN"]
            cfg.sck_pin = config_dict["SCK_PIN"]
            cfg.samples = config_dict["NUM_SAMPLES"]
            cfg.ref_unit = config_dict["REF_UNIT"]
            cfg.offset = config_dict["OFFSET"]
            cfg.min_weight = config_dict["MIN_WEIGHT"]
            cfg.max_weight = config_dict["MAX_WEIGHT"]
        except KeyError as e:
            print(f"Config file is missing required value: {e}")
            sys.exit(1)
        return cfg


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", help="The path to the config file")
    ap.add_argument("-i", "--influx", action="store_true", help="Log a point to influx")
    return ap.parse_args()


def current_weight(config):
    hx = SimpleHX711(config.dt_pin, config.sck_pin, config.ref_unit, config.offset)
    # hx.setUnit(Mass.Unit.LB)
    return hx.weight(config.samples)


def printLineProto(weight, percent_full):
    measurement = "scale"
    tags = {"name": "kitchen_keg"}
    tagStr = ",".join(f"{k}={v}" for k, v in tags.items())
    fields = {"raw_weight": weight,
              "percent_full": percent_full}
    fieldStr = ",".join(f"{k}={v}" for k, v in fields.items())
    print(f"{measurement},{tagStr} {fieldStr}")
    pass


def percent_full(weight, min_weight, max_weight):
    # The scale isn't perfect, if it's over max weight just assume it's full
    if weight > max_weight:
        return 100.0
    return (weight - min_weight) / (max_weight - min_weight) * 100


if __name__ == "__main__":
    args = parse_args()
    cfg = Config.from_yaml(args.config)
    weight = float(current_weight(cfg))
    fill_percent = percent_full(weight, cfg.min_weight, cfg.max_weight)

    if args.influx:
        printLineProto(weight, fill_percent)
    else:
        print(f"Current weight is: {weight}")
        print(f"Current fill percent is: {fill_percent}")
