import json
from dataclasses import dataclass
from os.path import isfile

@dataclass
class Patrons:
    _filepath       : str
    enthusiastic    : list[str]
    amazing         : list[str]
    legendary       : list[str]
    paypal          : list[str]

    def write(self):
        with open(self._filepath, "w") as f:
            toSerialize = _SerializablePatrons(self)
            json.dump(toSerialize.__dict__, f, indent=4)

def read(filepath: str) -> Patrons:
    if not isfile(filepath):
        return Patrons(
            _filepath = filepath,
            enthusiastic = [],
            amazing = [],
            legendary = [],
            paypal = []
        )
    with open(filepath, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"Failed to load {filepath}, returning default values")
            return Patrons(
                _filepath = filepath,
                enthusiastic = [],
                amazing = [],
                legendary = [],
                paypal = []
            )
    return Patrons(
        _filepath = filepath,
        enthusiastic = data['enthusiastic'],
        amazing = data['amazing'],
        legendary = data['legendary'],
        paypal = data['paypal']
    )

@dataclass
class _SerializablePatrons:
    enthusiastic    : list[str]
    amazing         : list[str]
    legendary       : list[str]
    paypal          : list[str]

    def __init__(self, patrons: Patrons) -> None:
        self.enthusiastic = patrons.enthusiastic
        self.amazing = patrons.amazing
        self.legendary = patrons.legendary
        self.paypal = patrons.paypal

if __name__ == "__main__":
    patronfile = read("./test.patrons.json")

    patronfile.write()