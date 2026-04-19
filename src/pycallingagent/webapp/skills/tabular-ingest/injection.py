from IPython import get_ipython

from pycallingagent.runtime import Function


def _ns():
    shell = get_ipython()
    return shell.user_ns if shell else {}


def list_dataframes():
    frames = _ns().get("dataframes", {})
    return {
        name: {"rows": len(frame), "columns": [str(column) for column in frame.columns.tolist()]}
        for name, frame in frames.items()
    }


def save_dataframe_artifact(df, name: str, format: str = "csv"):
    workspace = _ns()["workspace"]
    return workspace.save_dataframe(df, name, format=format)


__exports__ = [
    Function(list_dataframes),
    Function(save_dataframe_artifact),
]
