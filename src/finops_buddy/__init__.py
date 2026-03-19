"""FinOps Agent — CLI-first AWS cost visibility and analysis."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("finops-buddy")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"
