from IPython import get_ipython

from pycallingagent.runtime import Function


def _ns():
    shell = get_ipython()
    return shell.user_ns if shell else {}


def list_tickers():
    return _ns().get("tickers", [])


def get_market_snapshot(ticker: str):
    return _ns().get("research_data", {}).get(ticker, {}).get("market_snapshot", {})


def get_price_history(ticker: str):
    return _ns().get("price_history", {}).get(ticker)


def list_macro_series():
    return list(_ns().get("macro_series", {}).keys())


def get_news_items(ticker: str):
    return _ns().get("news_items", {}).get(ticker, [])


__exports__ = [
    Function(list_tickers),
    Function(get_market_snapshot),
    Function(get_price_history),
    Function(list_macro_series),
    Function(get_news_items),
]
