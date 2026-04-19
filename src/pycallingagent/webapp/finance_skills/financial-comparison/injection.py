from IPython import get_ipython

from pycallingagent.runtime import Function


def _ns():
    shell = get_ipython()
    return shell.user_ns if shell else {}


def get_comparison_frame():
    return _ns().get("comparison_frame")


def save_comparison_artifact(name: str = "comparison", format: str = "csv"):
    workspace = _ns()["workspace"]
    frame = _ns().get("comparison_frame")
    return workspace.save_dataframe(frame, name, format=format)


def save_custom_frame(df, name: str, format: str = "csv"):
    workspace = _ns()["workspace"]
    return workspace.save_dataframe(df, name, format=format)


__exports__ = [
    Function(get_comparison_frame),
    Function(save_comparison_artifact),
    Function(save_custom_frame),
]
