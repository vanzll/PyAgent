from IPython import get_ipython

from cave_agent.runtime import Function


def _ns():
    shell = get_ipython()
    return shell.user_ns if shell else {}


def get_company_profile(ticker: str):
    return _ns().get("research_data", {}).get(ticker, {}).get("profile", {})


def get_company_facts(ticker: str):
    sec_profile = _ns().get("research_data", {}).get(ticker, {}).get("sec_profile", {})
    return sec_profile.get("company_facts", {})


def get_recent_filings(ticker: str):
    sec_profile = _ns().get("research_data", {}).get(ticker, {}).get("sec_profile", {})
    return sec_profile.get("recent_filings", [])


__exports__ = [
    Function(get_company_profile),
    Function(get_company_facts),
    Function(get_recent_filings),
]
