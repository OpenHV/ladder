from setuptools import find_packages, setup

setup(
    name='openhv-ladder',
    version='0.1',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        "filelock",
        "flask",
        "numpy",
        "pyyaml",
        "trueskill",
        "pytest",
    ],
    entry_points=dict(
        console_scripts=[
            "openhv-ladder = tools.ladder:run",
            "ora-dbtool  = tools.ladder:initialize_periodic_databases",
            "openhv-replay = tools.replay:run",
        ],
    ),
)
