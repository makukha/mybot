# list of all plugin files installed
from . import talk


local_values = dict(locals()).values()
import inspect
skill_modules = [m for m in local_values if inspect.ismodule(m)]

import itertools
from .base import BaseSkill
skills = list(itertools.chain(*((v for k, v in m.__dict__.items() if k == 'Skill') for m in skill_modules)))

__all__ = ['skills']
