import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os.path
from tqdm import tqdm
from typing import List, Union
from datetime import datetime
from matplotlib.collections import LineCollection

AU = 149.6e9


class TrajectoryParticle:
    defaultcolor = "#F9F8F8"

    def __init__(
        self,
        name,
        dataFile: str,
        color: str,
        customData=None,
        colorHistory=True,
        tracerOn=True,
    ) -> None:
        self.name = name
        self.color = color
        self.tracerOn = tracerOn
        # self.colorHistory = colorHistory
        if colorHistory:
            self.histColor = color
        else:
            self.histColor = TrajectoryParticle.defaultcolor

        if customData is None:
            data = self._readDataFile(dataFile)
        else:
            data = customData

        self.timeData = data.loc[:, ["t"]]
        self.posData = data.loc[:, ["x", "y", "z"]]

        self.startTime = self.timeData.t.iloc[0]
        self.endTime = self.timeData.t.iloc[-1]

        self.line = None
        self.tracer = None
        # print(self.posData)

    def _readDataFile(
        self,
        dataFile: str,
    ):
        if dataFile[-3:] == "dat":
            delimiter = "   "
            delimiter = "\t"
        elif dataFile[-3:] == "csv":
            delimiter = ","
        else:
            raise ValueError("dataFile type is not supported (only .dat and .csv)")

        data = pd.read_csv(
            dataFile,
            delimiter=delimiter,
            names=["t", "x", "y", "z", "vx", "vy", "vz"],
            header=None,
        ).drop(["vx", "vy", "vz"], axis=1)

        return data

    def _dropBySpeed(self, speed: int):
        self.timeData = self.timeData.iloc[::speed]
        self.posData = self.posData.iloc[::speed]

    def _updateLine(self, time):
        # print(time, self.startTime, self.endTime)
        if (time >= self.startTime) and (time <= self.endTime):
            idx = self.timeData.query("t < @time").index

            temp = self.posData.loc[idx]
            tempTracer = self.posData.loc[idx[-8::]]

            self.line.set_data(temp.x, temp.y)  # , color=self.color)
            self.line.set_3d_properties(temp.z)
            self.line.set_color(self.histColor)
            self.line.set_alpha(1)
            # self.line.set_linewidth(0.7)
            if self.tracerOn:
                self.tracer.set_data(tempTracer.x, tempTracer.y)  # , color=self.color)
                self.tracer.set_3d_properties(tempTracer.z)
                self.tracer.set_color(self.color)
                self.tracer.set_linewidth(1.4)

                self.line.set_alpha(0.2)

        if time > self.endTime:
            if self.tracerOn:
                idx = self.timeData.query("t < @time").index
                tempTracer = self.posData.loc[idx[-2::]]
                self.tracer.set_data(tempTracer.x, tempTracer.y)  # , color=self.color)
                self.tracer.set_3d_properties(tempTracer.z)
                # if time-self.startTime > (self.endTime-self.startTime)/2:
                #     self.line.set_color(self.color)


class TrajectoryAnimator:
    def __init__(
        self,
        particles: List[TrajectoryParticle],
        plotLimits=AU,
        dpi=96,
        dt=3600,
        speed=50,
        # camera:Union[CameraSequence, None] = None
        camera=None,
    ) -> None:
        plt.style.use("dark_background")

        self.plotLimits = plotLimits

        self.dpi = dpi
        self.fig = plt.figure(figsize=(1920 / dpi, 1080 / dpi), dpi=dpi)

        self.ax = self.fig.add_subplot(111, projection="3d")

        self.ax.set_ylim(-plotLimits, plotLimits)
        self.ax.set_xlim(-plotLimits, plotLimits)
        self.ax.set_zlim(-plotLimits / 2, plotLimits / 2)

        self.particles = particles

        endTime = -1000
        startTime = 1e20

        for idx, particle in enumerate(self.particles):
            if particle.tracerOn:
                particle.line = self.ax.plot([], [], [], clip_on=False)[0]  # type: ignore
                particle.tracer = self.ax.plot([], [], [], markevery=[-1], marker="o", clip_on=False)[0]  # type: ignore
            else:
                particle.line = self.ax.plot([], [], [], marker="o", markevery=[-1], clip_on=False)[0]  # type: ignore

            self.fig.text(
                x=0.07,
                y=0.9 - (0.02 * idx),
                s=particle.name,
                color=particle.color,
                fontsize=14,
            )

            particle._dropBySpeed(speed)

            startTime = min(startTime, particle.timeData.t.iloc[0])
            endTime = max(endTime, particle.timeData.t.iloc[-1])

        self.lines = [particle.line for particle in self.particles]

        self.timeData = np.arange(startTime, endTime, int(dt * speed))

        J2000inUnix = 946684800
        self.dates = pd.to_datetime(self.timeData + J2000inUnix, unit="s").strftime(
            "%Y-%m-%d"
        )

        self.totalSteps = len(self.timeData)
        self.fig.tight_layout()
        # self.leftText = self.fig.text(x = 0.01, y=0.98, s=leftText)
        self.fig.subplots_adjust(0, 0, 1, 1)
        self.ax.set_box_aspect((2, 2, 1), zoom=2.4)
        self.ax.set_axis_off()
        # plt.axis("off")

    def _animateFunction(self, i):
        self.ax.view_init(elev=15.0, azim=-130)
        self.ax.set_title(self.dates[i], y=0.983, fontsize=14)

        for particle in self.particles:
            particle._updateLine(self.timeData[i])
        return self.lines

    def runAnimation(self, savefile="anim", fps=120):
        fullSaveName = "animations/" + savefile + ".mp4"
        print("Saving to " + fullSaveName)

        anim = FuncAnimation(
            self.fig,
            self._animateFunction,
            frames=tqdm(range(self.totalSteps)),
            interval=1,
            blit=True,
        )

        if not os.path.exists("animations"):
            os.makedirs("animations")

        anim.save(
            fullSaveName, fps=fps, extra_args=["-vcodec", "libx264"], dpi=self.dpi
        )


class CameraSequence:
    def __init__(self) -> None:
        self.sequence = []
        self.endTimes = []

    def __str__(self) -> str:
        res = "Camera Sequence: \n"
        for idx, u in enumerate(self.sequence):
            res += f"{idx} | {u[0]} | elev = {u[1][0]} | azi = {u[1][1]} | roll = {u[1][2]}\n"
        return res

    def addSegment(
        self, toFrac: float, elevation: float, azimuth: float, roll: float = 0
    ) -> None:
        segment = [toFrac, [elevation, azimuth, roll]]
        self.endTimes.append(toFrac)
        self.sequence.append(segment)

    def clearSequence(self) -> None:
        self.sequence = []


if __name__ == "__main__":
    thing1 = TrajectoryParticle(
        "Solar Sail 1 | Mass = 400 | Area = 12000",
        r"data/mass400_area12000.dat",
        "#d1495b",
        tracerOn=True,
        colorHistory=True,
    )
    thing2 = TrajectoryParticle(
        "Solar Sail 2 | Mass = 700 | Area = 10000",
        r"data/mass700_area10000.dat",
        "#26C485",
        tracerOn=True,
        colorHistory=True,
    )

    camera = CameraSequence()
    camera.addSegment(0, 90, -130)
    camera.addSegment(0.5, 90, -130)
    camera.addSegment(0.6, 15, -130)
    camera.addSegment(1, 15, -130)

    print(camera)
    traj = TrajectoryAnimator([thing1, thing2], speed=40)

    traj.runAnimation()
