from setuptools import setup, find_packages

setup(
    name='ch584_tool',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'click',
        'pyserial',
        'intelhex',
    ],
    entry_points={
        'console_scripts': [
            'ch584-flash=ch584_tool.cli:main',
        ],
    },
)
