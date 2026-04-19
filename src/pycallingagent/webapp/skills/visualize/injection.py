import matplotlib.pyplot as plt
from IPython import get_ipython

from pycallingagent.runtime import Function


def _ns():
    shell = get_ipython()
    return shell.user_ns if shell else {}


def plot_frame(df_name: str, kind: str, x: str, y: str, title: str, filename: str):
    frames = _ns().get("dataframes", {})
    workspace = _ns()["workspace"]
    frame = frames[df_name]
    figure, axis = plt.subplots(figsize=(8, 4.8))
    if kind == "line":
        frame.plot(x=x, y=y, kind="line", ax=axis, legend=False)
    elif kind == "bar":
        frame.plot(x=x, y=y, kind="bar", ax=axis, legend=False)
    elif kind == "scatter":
        frame.plot(x=x, y=y, kind="scatter", ax=axis)
    elif kind == "hist":
        frame[y].plot(kind="hist", ax=axis)
    else:
        raise ValueError(f"Unsupported chart kind: {kind}")
    axis.set_title(title)
    saved_path = workspace.save_chart(figure, filename)
    plt.close(figure)
    return saved_path


__exports__ = [
    Function(plot_frame),
]
