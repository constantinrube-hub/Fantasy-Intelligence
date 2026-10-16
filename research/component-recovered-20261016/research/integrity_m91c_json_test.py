#!/usr/bin/env python3
import json
import numpy as np
import pandas as pd
from build_m91c_season_challenger import json_safe

payload={
    "ok":1.25,
    "nan":float("nan"),
    "pos_inf":float("inf"),
    "neg_inf":float("-inf"),
    "np_nan":np.float64(np.nan),
    "pd_na":pd.NA,
    "nested":[1,np.float64(2.5),{"x":np.float64(np.nan)}],
}
safe=json_safe(payload)
assert safe["nan"] is None
assert safe["pos_inf"] is None
assert safe["neg_inf"] is None
assert safe["np_nan"] is None
assert safe["pd_na"] is None
assert safe["nested"][2]["x"] is None
json.dumps(safe,allow_nan=False)
print("PASS M9.1c strict JSON sanitization")
