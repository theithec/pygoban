INFO_PROPS = (
    "AN",
    "BR",
    "BT",
    "CP",
    "DT",
    "EV",
    "GC",
    "GN",
    "KM",
    "ON",
    "OT",
    "PB",
    "PC",
    "PW",
    "RE",
    "RO",
    "RU",
    "SO",
    "TM",
    "US",
    "WR",
    "WT",
)

ROOT_PROPS = ("AP", "CA", "FF", "GM", "ST", "SZ")
KEY_TYPES = {"SZ": int, "HA": int, "KM": float}
NODE_PROPS = (
    "N",
    "GW",
    "GB",
    "DM",
    "UC",
    "TE",
    "BM",
    "DO",
    "IT",
    "MN",
    "HO",
    "V",
)

PRESERVED_PROPS = ("KO", "FG", "PM", "VW")


class ParsingFailed(Exception):
    pass
