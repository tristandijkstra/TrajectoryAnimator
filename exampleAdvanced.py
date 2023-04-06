from trajectoryanimator.animator import (
    TrajectoryAnimator,
    TrajectoryParticle,
    CameraSequence,
)
import pandas as pd
import numpy as np

depVars = [
    "time",
    "ThrustX",
    "ThrustY",
    "ThrustZ",
    "ThrustMagnitude",
    "a",
    "e",
    "i",
    "omega",
    "RAAN",
    "theta",
    "cone",
    "clock",
]
temp = [x for x in range(18)]
depVars = depVars + temp
drops = [
    "ThrustX",
    "ThrustY",
    "ThrustZ",
    "ThrustMagnitude",
    "e",
    "omega",
    "RAAN",
    "theta",
    "cone",
    "clock",
]

yearInSeconds = 365 * 24 * 3600
AU = 149.6e9

extradata = pd.read_csv(
    r"data/best_dep.dat",
    delimiter="\t",
    header=None,
    names=depVars,
).drop(drops + temp, axis=1)
print(extradata.shape)
print(len(depVars))
print(extradata.head(3))
extradata = (
    extradata.assign(time=lambda x: ((x.time - extradata.time[0]) / yearInSeconds))
    .assign(a=lambda x: (x.a / AU).apply("{:.2f}".format) + " AU")
    .assign(i=lambda x: (np.degrees(x.i)).apply("{:.2f}".format) + r"°")
    .assign(time=lambda x: (x.time).apply("{:.2f}".format) + " yrs")
    .rename(
        columns={"a": "Semi-major Axis", "i": "Inclination", "time": "Time Elapsed"}
    )
)
print(extradata.tail())

sail = TrajectoryParticle(
    "Solar Surfer",
    r"data/best.dat",
    "#ef476f",
    tracerOn=True,
    colorHistory=False,
    extraData=extradata,
)
earth = TrajectoryParticle(
    "Earth",
    r"data/Earth.dat",
    "#249DAB",
    tracerOn=False,
    colorHistory=True,
)
venus = TrajectoryParticle(
    "Venus",
    r"data/Venus.dat",
    "#06D6A0",
    tracerOn=False,
    colorHistory=True,
)
mercury = TrajectoryParticle(
    "Mercury",
    r"data/Mercury.dat",
    "#FFD166",
    tracerOn=False,
    colorHistory=True,
)


camera = CameraSequence()
camera.addSegment(0, 15, 90)
# camera.addSegment(0.15, 90, 90, zoom=1.2)
camera.addSegment(0.38, 15, 90)
camera.addSegment(0.4, 15, 90)
camera.addSegment(0.50, 15, 90)
camera.addSegment(1, 15, 90)
camera.addSegment(1.05, 15, 135)
camera.addSegment(1.1, 15, 135)
# camera.addSegment(1.05, 15, 90)

traj = TrajectoryAnimator(
    particles=[sail, earth, venus, mercury],
    speed=40,
    camera=camera,
    dpi=96,
    centralBodyColor="#FFC300",
)

traj.runAnimation(fps=180, fileExtension="mp4")
# traj.runAnimation(fps=240, fileExtension="gif")
