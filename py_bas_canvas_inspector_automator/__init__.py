""" Package for automating the Canvas Inspector """
from .automator.automator import Automator
from .helpers import find_proc

__all__ = ["find_proc", "Automator"]
