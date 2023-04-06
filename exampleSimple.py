from trajectoryanimator.animator import (
    TrajectoryAnimator,
    TrajectoryParticle,
)


sail = TrajectoryParticle(
    "Solar Surfer",
    r"data/best.dat",
    "#ef476f",
    tracerOn=True,
    colorHistory=False,
)
earth = TrajectoryParticle(
    "Earth",
    r"data/Earth.dat",
    "#249DAB",
    tracerOn=False,
    colorHistory=True,
)
traj = TrajectoryAnimator(
    particles=[sail, earth],
    speed=40,
)

traj.runAnimation(fps=180, fileExtension="mp4")
# traj.runAnimation(fps=240, fileExtension="gif")
