# TrajectoryAnimator (WIP)
General Purpose Matplotlib-based trajectory animator. 
Generate eye-catching trajectory animations with high level code. 
Software is work in progress, documentation to follow.

### Examples
Two examples can be found here: [Advanced](exampleAdvanced.py) and [Simplified](exampleSimple.py). For now, the software is tailored to use results from Tudat, the TU Delft Aerospace Astrodynamics package. Other formats will follow. Basic data should have the format:

1. J2000 epoch time [s]
2. x [m]
3. y [m]
4. z [m]
5. vx [m/s]
6. vy [m/s]
7. vz [m/s]


### Results
Here is an output from the [advanced example](exampleAdvanced.py):

![Animation](doc/anim.gif)