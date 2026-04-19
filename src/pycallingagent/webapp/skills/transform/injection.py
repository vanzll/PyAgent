import re

from IPython import get_ipython

from pycallingagent.runtime import Function


def _ns():
    shell = get_ipython()
    return shell.user_ns if shell else {}


def standardize_columns(df):
    renamed = df.copy()
    renamed.columns = [
        re.sub(r"[^a-z0-9]+", "_", str(column).strip().lower()).strip("_")
        for column in renamed.columns
    ]
    return renamed


def merge_frames(left_name: str, right_name: str, on, how: str = "inner", output_name: str | None = None):
    frames = _ns().get("dataframes", {})
    merged = frames[left_name].merge(frames[right_name], on=on, how=how)
    if output_name:
        frames[output_name] = merged
    return merged


__exports__ = [
    Function(standardize_columns),
    Function(merge_frames),
]
