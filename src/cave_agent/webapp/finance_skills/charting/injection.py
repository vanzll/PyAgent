import matplotlib.pyplot as plt
from IPython import get_ipython

from cave_agent.runtime import Function


def _ns():
    shell = get_ipython()
    return shell.user_ns if shell else {}


def plot_price_history(ticker: str, filename: str = "price-history"):
    price_history = _ns().get("price_history", {}).get(ticker)
    workspace = _ns()["workspace"]
    if price_history is None or price_history.empty:
        raise ValueError(f"No price history for {ticker}")
    figure, axis = plt.subplots(figsize=(8, 4.8))
    axis.plot(price_history["date"], price_history["adjusted_close"], label=ticker)
    axis.set_title(f"{ticker} Price History")
    axis.set_ylabel("Adjusted Close")
    axis.tick_params(axis="x", rotation=45)
    axis.legend()
    saved = workspace.save_chart(figure, filename)
    plt.close(figure)
    return saved


def plot_relative_performance(filename: str = "normalized-returns"):
    price_history = _ns().get("price_history", {})
    workspace = _ns()["workspace"]
    figure, axis = plt.subplots(figsize=(8, 4.8))
    for ticker, frame in price_history.items():
        if frame.empty:
            continue
        base = float(frame.iloc[0]["adjusted_close"])
        normalized = (frame["adjusted_close"] / base) * 100.0 if base else frame["adjusted_close"]
        axis.plot(frame["date"], normalized, label=ticker)
    axis.set_title("Relative Performance")
    axis.set_ylabel("Normalized Return")
    axis.tick_params(axis="x", rotation=45)
    axis.legend()
    saved = workspace.save_chart(figure, filename)
    plt.close(figure)
    return saved


__exports__ = [
    Function(plot_price_history),
    Function(plot_relative_performance),
]
