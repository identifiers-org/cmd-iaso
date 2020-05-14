from setuptools import setup

setup(
    name="cmd-iaso",
    version="0.0.1",
    entry_points={"console_scripts": ["cmd-iaso = iaso.cli:main",],},
    packages=["iaso"],
    package_data={"iaso.curation.pyppeteer": ["*.js", "*.css"]},
    install_requires=[
        "click==7.1.2",
        "jsonschema==3.2.0",
        "psutil==5.7.0",
        "py-cpuinfo==5.0.0",
        "pyppeteer==0.0.25",
        "requests==2.23.0",
    ],
    author="Moritz Langenstein",
    license="MIT License",
    python_requires=">=3.6",
)
