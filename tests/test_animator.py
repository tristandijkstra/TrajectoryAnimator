from trajectoryanimator.animator import (
    CameraSequence,
    TrajectoryAnimator,
    TrajectoryParticle,
)


def testCamera():
    camera = CameraSequence()
    camera.addSegment(0, 15, 90)
    camera.addSegment(0.38, 15, 90)
    camera.addSegment(0.4, 15, 90)
    camera.addSegment(0.50, 15, 90)
    camera.addSegment(1, 15, 90)
    camera.addSegment(1.05, 15, 135)
    camera.addSegment(1.1, 15, 135)
