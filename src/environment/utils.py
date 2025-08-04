# -*- coding: utf-8 -*-
"""
Utility functions and variables.

This file is part of the pokemon showdown reinforcement learning bot project,
created by Randy Kotti, Ombeline Lagé and Haris Sahovic as part of their
advanced topics in artifical intelligence course at Ecole Polytechnique.
"""

import json
import numpy as np

from typing import Generator
PATH = "/home/denso/reinforcement-learning-pokemon-bot/"

CATEGORIES = ["Physical", "Special", "Status"]
"""List of str: move categories"""

CONFIG_PATH = "config.json"
"""str: path to the config file"""

with open(PATH + CONFIG_PATH) as f:
    CONFIG = json.load(f)
    """dict: configuration dictionnary"""

TARGETS = [
    "any",
    "all",
    "randomNormal",
    "allAdjacent",
    "allyTeam",
    "normal",
    "self",
    "allAdjacentFoes",
    "allySide",
    "foeSide",
    "scripted",
]
"""List of str: possible target values for a move"""

TYPES = [
    "bug",
    "dark",
    "dragon",
    "electric",
    "fairy",
    "fighting",
    "fire",
    "flying",
    "ghost",
    "grass",
    "ground",
    "ice",
    "normal",
    "poison",
    "psychic",
    "rock",
    "steel",
    "water",
]
"""List of str: possible values for types"""

# TODO : add type chart

SECONDARIES = ["par", "brn", "frz", "psn", "slp", "flinch", "confusion"]
"""List of str: secondary effects a move can have"""

SEXES = ["F", "M", "N"]
"""List of str: possible values for pokemon sexes"""

with open(PATH + "data/moves.json") as f:
    # These are magic regexes to convert from the .js moves file to working json, when
    # combined with some auto-formatting
    # ^    "((on.*)|(.*Callback))": function\(.*?\) {\n(.*\n)*?    },\n
    # ^      "((on.*)|(.*Callback))": function\(.*?\) {\n(.*\n)*?      },?\n
    # ^        "((on.*)|(.*Callback))": function\(.*?\) {\n(.*\n)*?        },?\n
    # //.*

    MOVES = json.load(f)
    """dict: move information, imported from Pokemon Showdown"""

# 第9世代の技を追加
GEN9_MOVES = {
    "bodypress": {
        "name": "bodypress",
        "type": "fighting",
        "target": "normal",
        "basePower": 80,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0
    },
    "jetpunch": {
        "name": "jetpunch",
        "type": "water",
        "target": "normal",
        "basePower": 60,
        "accuracy": 100,
        "pp": 20,
        "category": "Physical",
        "priority": 1
    },
    "trailblaze": {
        "name": "trailblaze",
        "type": "grass",
        "target": "normal",
        "basePower": 50,
        "accuracy": 100,
        "pp": 20,
        "category": "Physical",
        "priority": 0
    },
    "terablast": {
        "name": "terablast",
        "type": "normal",
        "target": "normal",
        "basePower": 80,
        "accuracy": 100,
        "pp": 10,
        "category": "Special",
        "priority": 0
    },
    "dragonenergy": {
        "name": "dragonenergy",
        "type": "dragon",
        "target": "allAdjacentFoes",
        "basePower": 150,
        "accuracy": 100,
        "pp": 5,
        "category": "Special",
        "priority": 0
    },
    "supercellslam": {
        "name": "supercellslam",
        "type": "electric",
        "target": "normal",
        "basePower": 100,
        "accuracy": 95,
        "pp": 15,
        "category": "Physical",
        "priority": 0
    },
    "noretreat": {
        "name": "noretreat",
        "type": "fighting",
        "target": "self",
        "basePower": 0,
        "accuracy": 100,
        "pp": 5,
        "category": "Status",
        "priority": 0
    },
    "psychicnoise": {
        "name": "psychicnoise",
        "type": "psychic",
        "target": "normal",
        "basePower": 75,
        "accuracy": 100,
        "pp": 10,
        "category": "Special",
        "priority": 0
    },
    "bittermalice": {
        "name": "bittermalice",
        "type": "ghost",
        "target": "normal",
        "basePower": 75,
        "accuracy": 100,
        "pp": 10,
        "category": "Special",
        "priority": 0
    },
    "shelter": {
        "name": "shelter",
        "type": "steel",
        "target": "self",
        "basePower": 0,
        "accuracy": 100,
        "pp": 10,
        "category": "Status",
        "priority": 0
    },
    "triplearrows": {
        "name": "triplearrows",
        "type": "fighting",
        "target": "normal",
        "basePower": 90,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0
    },
    "infernalparade": {
        "name": "infernalparade",
        "type": "ghost",
        "target": "normal",
        "basePower": 60,
        "accuracy": 100,
        "pp": 15,
        "category": "Special",
        "priority": 0
    },
    "flipturn": {
        "name": "flipturn",
        "type": "water",
        "target": "normal",
        "basePower": 60,
        "accuracy": 100,
        "pp": 20,
        "category": "Physical",
        "priority": 0
    },
    "revivalblessing": {
        "name": "revivalblessing",
        "type": "normal",
        "target": "self",
        "basePower": 0,
        "accuracy": 100,
        "pp": 1,
        "category": "Status",
        "priority": 0
    },
    "ceaselessedge": {
        "name": "ceaselessedge",
        "type": "dark",
        "target": "normal",
        "basePower": 65,
        "accuracy": 90,
        "pp": 15,
        "category": "Physical",
        "priority": 0
    },
    "bleakwindstorm": {
        "name": "bleakwindstorm",
        "type": "flying",
        "target": "allAdjacentFoes",
        "basePower": 100,
        "accuracy": 80,
        "pp": 10,
        "category": "Special",
        "priority": 0
    },
    "wildboltstorm": {
        "name": "wildboltstorm",
        "type": "electric",
        "target": "allAdjacentFoes",
        "basePower": 100,
        "accuracy": 80,
        "pp": 10,
        "category": "Special",
        "priority": 0
    },
    "sandsearstorm": {
        "name": "sandsearstorm",
        "type": "ground",
        "target": "allAdjacentFoes",
        "basePower": 100,
        "accuracy": 80,
        "pp": 10,
        "category": "Special",
        "priority": 0
    },
    "lunarblessing": {
        "name": "lunarblessing",
        "type": "psychic",
        "target": "allyTeam",
        "basePower": 0,
        "accuracy": 100,
        "pp": 5,
        "category": "Status",
        "priority": 0
    },
    "takeheart": {
        "name": "takeheart",
        "type": "psychic",
        "target": "self",
        "basePower": 0,
        "accuracy": 100,
        "pp": 10,
        "category": "Status",
        "priority": 0
    },
    "gigatonhammer": {
        "name": "gigatonhammer",
        "type": "steel",
        "target": "normal",
        "basePower": 160,
        "accuracy": 100,
        "pp": 5,
        "category": "Physical",
        "priority": 0
    },
    "comeuppance": {
        "name": "comeuppance",
        "type": "dark",
        "target": "normal",
        "basePower": 0,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0
    },
    "aquacutter": {
        "name": "aquacutter",
        "type": "water",
        "target": "normal",
        "basePower": 70,
        "accuracy": 100,
        "pp": 20,
        "category": "Physical",
        "priority": 0
    },
    "blazingtorque": {
        "name": "blazingtorque",
        "type": "fire",
        "target": "normal",
        "basePower": 80,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0
    },
    "wickedtorque": {
        "name": "wickedtorque",
        "type": "dark",
        "target": "normal",
        "basePower": 80,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0
    },
    "noxioustorque": {
        "name": "noxioustorque",
        "type": "poison",
        "target": "normal",
        "basePower": 100,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0
    },
    "combattorque": {
        "name": "combattorque",
        "type": "fighting",
        "target": "normal",
        "basePower": 100,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0
    },
    "magicaltorque": {
        "name": "magicaltorque",
        "type": "fairy",
        "target": "normal",
        "basePower": 100,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0
    },
    "icespinner": {
        "name": "icespinner",
        "type": "ice",
        "target": "normal",
        "basePower": 80,
        "accuracy": 100,
        "pp": 15,
        "category": "Physical",
        "priority": 0
    },
    "wavecrash": {
        "name": "wavecrash",
        "type": "water",
        "target": "normal",
        "basePower": 120,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0
    },
    "snowscape": {
        "name": "snowscape",
        "type": "ice",
        "target": "all",
        "basePower": 0,
        "accuracy": True,
        "pp": 10,
        "category": "Status",
        "priority": 0,
    },
    "chillyreception": {
        "name": "chillyreception",
        "type": "ice",
        "target": "self",
        "basePower": 0,
        "accuracy": True,
        "pp": 10,
        "category": "Status",
        "priority": 0,
    },
    "shedtail": {
        "name": "shedtail",
        "type": "normal",
        "target": "self",
        "basePower": 0,
        "accuracy": True,
        "pp": 10,
        "category": "Status",
        "priority": 0,
    },
    "populationbomb": {
        "name": "populationbomb",
        "type": "normal",
        "target": "normal",
        "basePower": 20,
        "accuracy": 90,
        "pp": 10,
        "category": "Physical",
        "priority": 0,
    },
    "aquastep": {
        "name": "aquastep",
        "type": "water",
        "target": "normal",
        "basePower": 80,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0,
    },
    "ragingbull": {
        "name": "ragingbull",
        "type": "normal",
        "target": "normal",
        "basePower": 90,
        "accuracy": 100,
        "pp": 10,
        "category": "Physical",
        "priority": 0,
    },
    "makeitrain": {
        "name": "makeitrain",
        "type": "steel",
        "target": "allAdjacentFoes",
        "basePower": 120,
        "accuracy": 100,
        "pp": 5,
        "category": "Special",
        "priority": 0,
    },
    "psyblade": {
        "name": "psyblade",
        "type": "psychic",
        "target": "normal",
        "basePower": 80,
        "accuracy": 100,
        "pp": 15,
        "category": "Physical",
        "priority": 0,
    },
    "hydrosteam": {
        "name": "hydrosteam",
        "type": "water",
        "target": "normal",
        "basePower": 80,
        "accuracy": 100,
        "pp": 15,
        "category": "Special",
        "priority": 0,
    },
    "ruination": {
        "name": "ruination",
        "type": "dark",
        "target": "normal",
        "basePower": 0,
        "accuracy": 90,
        "pp": 10,
        "category": "Special",
        "priority": 0,
    },
    "collisioncourse": {
        "name": "collisioncourse",
        "type": "fighting",
        "target": "normal",
        "basePower": 100,
        "accuracy": 100,
        "pp": 5,
        "category": "Physical",
        "priority": 0,
    },
    "electrodrift": {
        "name": "electrodrift",
        "type": "electric",
        "target": "normal",
        "basePower": 100,
        "accuracy": 100,
        "pp": 5,
        "category": "Special",
        "priority": 0,
    },
    "dualwingbeat": {
        "type": "flying",
        "category": "physical",
        "pp": 10,
        "accuracy": 90,
        "priority": 0,
        "flags": {"protect", "mirror", "distance"},
        "secondary": None,
        "target": "any",
        "description": "The user slams the target with its wings. The target is hit twice in a row."
    },
    "scorchingsands": {
        "type": "ground",
        "category": "special",
        "pp": 10,
        "accuracy": 80,
        "priority": 0,
        "flags": {"protect", "mirror", "defrost"},
        "secondary": {"chance": 30, "status": "brn"},
        "target": "any",
        "description": "The user throws scorching sand at the target. This may also leave the target with a burn."
    },
    "armorcannon": {
        "type": "fire",
        "category": "special",
        "pp": 5,
        "accuracy": 100,
        "priority": 0,
        "flags": {"protect", "mirror"},
        "secondary": None,
        "target": "any",
        "description": "The user shoots its own armor at its target. This also lowers the user's Defense and Sp. Def stats."
    },
    "alluringvoice": {
        "type": "fairy",
        "category": "special",
        "pp": 10,
        "accuracy": 100,
        "priority": 0,
        "flags": {"protect", "mirror", "sound"},
        "secondary": {"chance": 30, "volatileStatus": "confusion"},
        "target": "any",
        "description": "The user lets out a charming cry that may confuse the target."
    },
}

# 第8世代の技を追加
GEN8_MOVES = {
    "tripleaxel": {
        "name": "tripleaxel",
        "type": "ice",
        "target": "normal",
        "basePower": 20,
        "accuracy": 90,
        "pp": 10,
        "category": "Physical",
        "priority": 0
    },
    "poltergeist": {
        "name": "poltergeist",
        "type": "ghost",
        "target": "normal",
        "basePower": 110,
        "accuracy": 90,
        "pp": 5,
        "category": "Physical",
        "priority": 0
    },
    "psyblade": {
        "name": "psyblade",
        "type": "psychic",
        "target": "normal",
        "basePower": 80,
        "accuracy": 100,
        "pp": 15,
        "category": "Physical",
        "priority": 0
    }
}

# 既存の技データベースに新しい技を追加
MOVES.update(GEN9_MOVES)
MOVES.update(GEN8_MOVES)

with open(PATH + "data/pokedex.json") as f:
    POKEDEX = json.load(f)

# 新しいポケモンのデータを追加
with open(PATH + "data/new_pokemon.json") as f:
    new_pokemon = json.load(f)
    POKEDEX.update(new_pokemon)

def _data_yielder(data) -> Generator:
    """
    Generator yielding data in a deterministric way from an arbitrary nested data 
    container.

    Args:
        data (arbitrary): The data source.

    Yields:
        float: The next value in the data source.

    Examples:
        >>> data = {'a' : [1, 2, 3], 'b' : 4, 'd' : False}
        >>> print([el for el in _data_yielder(data)])
        [1.0, 2.0, 3.0, 4.0, 0.0]

    """
    if isinstance(data, int):
        yield data
    elif isinstance(data, bool):
        yield 1 if data else 0
    elif data is None:
        yield 0
    elif isinstance(data, float):
        yield data
    elif isinstance(data, dict):
        for key in sorted(data.keys()):
            for el in _data_yielder(data[key]):
                yield el
    elif isinstance(data, list):
        for el in data:
            for foo in _data_yielder(el):
                yield foo
    elif isinstance(data, tuple):
        for el in data:
            for foo in _data_yielder(el):
                yield foo
    else:
        raise ValueError(
            f"Type {type(data)} (with value {data}) is not compatible with function data_flattener"
        )


def data_flattener(data) -> list:
    """
    Returns a flattened list of values extracted from an arbitrary nested data
    container in a determinisstic way.

    Args:
        data (arbitrary): The data source.

    Returns:
        float: The flattened array with values from the data source.

    Examples:
        >>> data = {'a' : [1, 2, 3], 'b' : 4, 'd' : False}
        >>> data_flattener(data)
        [1.0, 2.0, 3.0, 4.0, 0.0]

    """
    return [el for el in _data_yielder(data)]
