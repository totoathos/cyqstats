from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

extensions = [
    Extension(
        "cyqstats._cycore",
        ["src/cyqstats/_cycore.pyx"],
        include_dirs=[np.get_include()],
    )
]

setup(
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
            "nonecheck": False,
            "initializedcheck": False,
        },
    )
)
