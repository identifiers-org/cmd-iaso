from setuptools import setup, find_packages

setup(
    name="cmd-iaso",
    version="0.0.1",
    entry_points={"console_scripts": ["cmd-iaso = iaso.cli:main",],},
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_data={"iaso.curation.pyppeteer": ["*.js", "*.css"]},
    install_requires=[
        "aioconsole==0.1.16",
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
