import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os
from tqdm import tqdm
from typing import List, Union
import datetime

astronomical_unit = 149.6e9  # m


class TrajectoryParticle:
    defaultcolor = "#F9F8F8"

    def __init__(
        self,
        name,
        color: str,
        time_data: Union[np.ndarray, list],
        position_data: Union[np.ndarray, list],
        extra_data: Union[np.ndarray, list, None] = None,
        extra_data_prefixes: Union[np.ndarray, list, None] = None,
        dim_history:bool=False,
        enable_tracer:bool=False,
        tracer_percentage:float=2,
        line_width:float=1,
        alpha:float=1,
    ) -> None:
        self.name = name
        self.color = color
        self.enable_tracer = enable_tracer
        self.alpha = alpha
        self.line_width = line_width

        self.timeData = time_data
        self.posData = position_data

        self.startTime = time_data[0]
        self.endTime = time_data[-1]

        # line colour
        if dim_history:
            self.histColor = TrajectoryParticle.defaultcolor
        else:
            self.histColor = color

        # length of tracer as percentage of the full line
        self.tracer_length = int(len(self.timeData) * (tracer_percentage / 100))
        if enable_tracer:
            self.alpha = self.alpha * 0.5

        # properties of the particle's line used in animation
        self.line = None
        self.tracer = None
        self.lightUp = False
        self.lightUpNum = 0

        # properties ofextra data to plot in top right
        if extra_data is not None:
            self.extra_data = extra_data
            self.extra_data_available = True
            self.extra_data_prefixes = extra_data_prefixes
            self.extra_data_text = ""
        else:
            self.extra_data_available = False

    def _updateLine(self, current_time:datetime.datetime):
        """Updates the line to be plotted.

        Args:
            time (datetime.datetime): current time in animation
        """
        if (current_time >= self.startTime) and (current_time <= self.endTime):
            # idxs of data that has already passed.
            # TODO this can be optimised. numpy arrays cant contain python datetimes
            # also numpy datetimes suck
            idxs = [i for i, x in enumerate(self.timeData) if (x <= current_time)]
            temp = self.posData[idxs, :]


            # update the line.
            self.line.set_data(temp[:, 0], temp[:, 1])
            self.line.set_3d_properties(temp[:, 2]) # sets the Z coordinate
            self.line.set_color(self.histColor)
            self.line.set_alpha(self.alpha)
            self.line.set_markersize(9)
            self.line.set_linewidth(1.0 * self.line_width)

            # update the tracer line if enabled
            if self.enable_tracer:
                tempTracer = self.posData[idxs[-self.tracer_length : :]]
                self.tracer.set_data(tempTracer[:, 0], tempTracer[:, 1])
                self.tracer.set_3d_properties(tempTracer[:, 2])
                self.tracer.set_color(self.color)
                self.tracer.set_linewidth(2 * self.line_width)
                self.tracer.set_markersize(9)
                
                self.line.set_alpha(self.alpha)

            # update extra data text
            if self.extra_data_available and len(idxs) > 0:
                temp = ""
                for idxExtra, prefix in enumerate(self.extra_data_prefixes):
                    temp += f"{prefix}{(self.extra_data[idxs[-1], idxExtra])}\n"
                self.extra_data_text = temp

        # at the end or beyond.
        if current_time > self.endTime:
            if self.enable_tracer:
                idxs = [i for i, x in enumerate(self.timeData) if (x <= current_time)]

                tempTracer = self.posData[idxs[-2::], :]
                self.tracer.set_data(tempTracer[:, 0], tempTracer[:, 1])
                self.tracer.set_3d_properties(tempTracer[:, 2])

        if self.lightUp and self.enable_tracer:
            self.line.set_color(self.color)
            self.line.set_alpha(min(1, self.alpha + (0.005 * self.lightUpNum)))
            self.lightUpNum += 1


class TrajectoryAnimator:
    def __init__(
        self,
        particles: List[TrajectoryParticle],
        plot_limits: float = astronomical_unit,
        speed: Union[float, int, None] = None,
        duration: Union[float, int, None] = None,
        fps: int = 60,
        dpi: int = 96,
        resolution:tuple = (1920, 1080),
        camera = None,
        time_format:str = "%Y-%m-%d",
        light_up: bool = True,
        central_body_color: Union[str, None] = None,
        watermark: Union[str, None] = None
    ) -> None:
        plt.style.use("dark_background")

        self.particles = particles
        self.camera = camera

        self.plot_limits = plot_limits
        self.time_format = time_format
        self.watermark = watermark

        self.speed = speed
        self.duration = duration
        self.fps = fps
        self.dpi = dpi

        self.light_up = light_up

        # create figure and subplot
        self.fig, self.ax = plt.subplots(
            1,
            1,
            figsize=(resolution[0] / dpi, resolution[1] / dpi),
            dpi=dpi,
            subplot_kw=dict(projection="3d"),
        )

        self.ax.set_ylim(-plot_limits, plot_limits)
        self.ax.set_xlim(-plot_limits, plot_limits)
        self.ax.set_zlim(-plot_limits / 2, plot_limits / 2)

        self.rightText = self.fig.text(
            x=0.95,
            y=0.95,
            s="",
            # color=particle.color,
            fontsize=22,
            horizontalalignment="right",
            fontfamily="monospace",
            verticalalignment="top",
        )

        self.titletext = self.fig.text(
            x=0.5,
            y=0.95,
            s="",
            fontsize=28,
            horizontalalignment="center",
            verticalalignment="top",
        )

        if self.watermark is not None:
            self.watermarktext = self.fig.text(
                x=0.95,
                y=0.05,
                s=self.watermark,
                fontsize=16,
                horizontalalignment="right",
                verticalalignment="bottom",
            )

        self.speed_text = self.fig.text(
            x=0.5,
            y=0.9,
            s="",
            fontsize=16,
            horizontalalignment="center",
            verticalalignment="top",
        )

        # TODO Will need to do this a smarter way in the future
        start_time = datetime.datetime(3000, 1, 1)
        end_time = datetime.datetime(1, 1, 1)
        # This goes through all the particles, initialiases their features and 
        # retrieves their start and end times to coordinate an overall start/end
        for idx, particle in enumerate(self.particles):
            if particle.enable_tracer:
                particle.line = self.ax.plot([], [], [], clip_on=False)[0]
                particle.tracer = self.ax.plot(
                    [],
                    [],
                    [],
                    markevery=[-1],
                    marker="o",
                    clip_on=False,
                )[0]
            else:
                particle.line = self.ax.plot(
                    [],
                    [],
                    [],
                    marker="o",
                    markevery=[-1],
                    clip_on=False,
                )[0]

            self.fig.text(
                x=0.05,
                y=0.95 - (0.035 * idx),
                s=particle.name,
                color=particle.color,
                fontsize=22,
                verticalalignment="top",
            )

            start_time = min(start_time, particle.timeData[0])
            end_time = max(end_time, particle.timeData[-1])

        self.start_time = start_time

        startTime_seconds = datetime.datetime.timestamp(start_time)
        endTime_seconds = datetime.datetime.timestamp(end_time)

        if camera is not None:
            time_multiplier = camera._get_multiplier()
        else:
            time_multiplier = 1

        self.total_seconds_orbit = (endTime_seconds - startTime_seconds)
        self.total_seconds_full = self.total_seconds_orbit * time_multiplier
        # user input handling for duration and speed
        if (self.duration is None) and (self.speed is None):
            raise ValueError("Either `duration` or `speed` must be not None")
        elif (self.duration is not None) and (self.speed is not None):
            raise ValueError("Parameters `duration` and `speed` are mutually exclusive")
        elif self.duration is not None:
            self.anim_duration = self.duration * time_multiplier
            self.speed = self.total_seconds_orbit / self.anim_duration / self.fps
        elif self.speed is not None:
            self.anim_duration = round((self.total_seconds_full / self.fps / self.speed) * time_multiplier)
            self.duration = self.anim_duration
        else:
            raise Exception("Unknown error")
        

        temp_full = int((self.total_seconds_full / self.speed) + 3)
        temp_orbit = int((self.total_seconds_orbit / self.speed) + 3)
        self.total_steps = temp_full
        self.total_steps_orbit = temp_orbit

        # get camera sequence
        if camera is not None:
            self.cameraSequence = camera._transformCamera(self.total_steps_orbit)

        # This removes padding
        self.fig.subplots_adjust(0, 0, 1, 1)
        # this changes the image's aspect ratio and zoom
        self.ax.set_box_aspect((2, 2, 1), zoom=2.4)
        # remove axis lines etc.
        self.ax.set_axis_off()

        # add a dot to the centre
        # TODO should add a more sophisticated dot to represent a larger plane
        if central_body_color is not None:
            self.ax.scatter(0, 0, 0, color=central_body_color, s=120)

        # Finalise the initialisation
        self.lines = [particle.line for particle in self.particles]
        # self.tracers = [particle.tracer for particle in self.particles]

            
    def animation_function(self, i):
        current_time = self.start_time + datetime.timedelta(
            seconds=(self.speed * (i - 1))
        )

        if self.camera is None:
            self.ax.view_init(elev=15.0, azim=-130)
        else:
            self.ax.set_box_aspect((2, 2, 1), zoom=self.cameraSequence[3][i])
            self.ax.view_init(
                self.cameraSequence[0][i],
                self.cameraSequence[1][i],
                self.cameraSequence[2][i],
            )

        for particle in self.particles:
            if i < self.total_steps_orbit:
                self.titletext.set_text(current_time.strftime(self.time_format))
                self.speed_text.set_text(f"{round(self.speed, 0)}x")
            particle._updateLine(current_time)

            if self.light_up and (i >= self.total_steps_orbit):
                particle.lightUp = True

            if particle.extra_data_available:
                # self.rightText.set_color(particle.histColor)
                self.rightText.set_text(particle.extra_data_text)

        return self.lines

    def run_animation(self, savefile):
        _, fileExtension = os.path.splitext(savefile)
        save_folder, _ = os.path.split(savefile)
        # check if folder exists:
        if not os.path.exists(path=save_folder):
            raise ValueError("Savefolder path does not exist")

        print("Saving to " + savefile)
        phys_time = datetime.timedelta(seconds=self.total_seconds_full)
        anim_time = datetime.timedelta(seconds=self.anim_duration)
        print(f"Physical Duration: {phys_time} | Animation Duration {anim_time}")

        anim = FuncAnimation(
            self.fig,
            self.animation_function,
            frames=tqdm(range(self.total_steps)),
            interval=100,
            blit=True,
        )

        if (fileExtension == ".gif") or (fileExtension == ".webm"):
            anim.save(savefile, fps=self.fps, dpi=self.dpi)

        elif fileExtension == ".mp4":
            anim.save(
                savefile, fps=self.fps, extra_args=["-vcodec", "libx264"], dpi=self.dpi
            )
        else:
            raise NotImplementedError(
                f"file extension {fileExtension} not implemented."
            )
        
        # TODO
        # clear items in lines.
        # for line in self.lines:
        #     line.set_data([], [])
        #     line.set_3d_properties([])
        # # for tracer in self.tracers:
        # #     tracer.set_data([], [])
        # #     tracer.set_3d_properties([])
        # self.rightText.set_text("")

        
            


class CameraSequence:
    def __init__(self) -> None:
        self.sequence = []
        self.endTimes = []
        self.extendPast = False
        self.max_end = 0

        self.finalSet: np.ndarray = None

    def __str__(self) -> str:
        res = "Camera Sequence: \n"
        for idx, u in enumerate(self.sequence):
            res += f"{idx} | {self.endTimes[0]} | elev = {u[0]} | azi = {u[1]} | roll = {u[2]}\n | zoom = {u[3]}\n"
        return res

    def addSegment(
        self,
        toFrac: float,
        elevation: float,
        azimuth: float,
        roll: float = 0,
        zoom: float = 2.4,
    ) -> None:
        segment = [elevation, azimuth, roll, zoom]
        self.endTimes.append(toFrac)
        self.sequence.append(segment)

    def clearSequence(self) -> None:
        self.sequence = []

    def bezier(self, x0: float, x1: float, t0: int, t1: int):
        if x1 == x0:
            return np.linspace(x0, x1, (t1 - t0))
        else:
            t = np.linspace(0, 1, (t1 - t0))
            arr = t * t * (3.0 - 2.0 * t)
            return (arr * (x1 - x0)) + x0
        
    def _get_multiplier(self):
        return max(self.endTimes)

    def _transformCamera(self, totalSteps):
        if max(self.endTimes) > 1:
            self.extendPast = True

        self.endTimes = [int(x * totalSteps) for x in self.endTimes]

        arrays = []
        lastStartTime = 0
        lastElev = 0
        lastAzi = 0
        lastRoll = 0
        lastZoom = 0

        for seqSet, endTime in zip(self.sequence, self.endTimes):
            # arrays += list(range(lastStartTime, ))
            if endTime == 0:
                lastElev, lastAzi, lastRoll, lastZoom = seqSet
            else:
                currentElev, currentAzi, currentRoll, currentZoom = seqSet

                elevArray = self.bezier(lastElev, currentElev, lastStartTime, endTime)
                aziArray = self.bezier(lastAzi, currentAzi, lastStartTime, endTime)
                rollArray = self.bezier(lastRoll, currentRoll, lastStartTime, endTime)
                zoomArray = self.bezier(lastZoom, currentZoom, lastStartTime, endTime)

                arrays.append(np.vstack([elevArray, aziArray, rollArray, zoomArray]))

                lastStartTime = endTime
                lastElev, lastAzi, lastRoll, lastZoom = seqSet

        self.finalSet = np.hstack(arrays)

        return self.finalSet


    # factory functions
    # def create_top_down(self, zoom=1, final_frac=1):
    #     self.__init__()
    #     self.addSegment(0.0, 0, 0, zoom = zoom)
    #     self.addSegment(final_frac, 0, 0, zoom = zoom)
    #     return self