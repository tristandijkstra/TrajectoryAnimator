from setuptools import find_packages, setup

setup(
    name='trajectoryanimator',
    packages=find_packages(include=['trajectoryanimator']),
    version='0.1.0',
    description='Spacecraft Trajectory Animator',
    author='Tristan Dijkstra',
    license='GNU GPLv3',
    install_requires=["numpy", "pandas", "matplotlib", "tqdm"],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
)