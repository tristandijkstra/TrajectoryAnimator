import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os.path
from tqdm import tqdm
from typing import List

AU = 149.6e9


class TrajectoryParticle:
    def __init__(self, name, dataFile:str, color:str, customData=None) -> None:
        self.name = name
        self.color = color

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


    def _readDataFile(self, dataFile:str,):
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
    
    def _dropBySpeed(self, speed:int):
        self.timeData = self.timeData.iloc[::speed]
        self.posData = self.posData.iloc[::speed]

    def _updateLine(self, time):
        # print(time, self.startTime, self.endTime)
        if (time >= self.startTime) and (time <= self.endTime):
            idx = self.timeData.query("t < @time").index
            
            temp = self.posData.loc[idx]
            tempTracer = self.posData.loc[idx[-8::]]
            
            self.line.set_data(temp.x, temp.y) #, color=self.color)
            self.line.set_3d_properties(temp.z)
            self.line.set_color(self.color)
            self.line.set_alpha(0.2)
            self.tracer.set_linewidth(0.7)

            self.tracer.set_data(tempTracer.x, tempTracer.y) #, color=self.color)
            self.tracer.set_3d_properties(tempTracer.z)
            self.tracer.set_color(self.color)
            self.tracer.set_linewidth(3)
        
        if (time > self.endTime):
            idx = self.timeData.query("t < @time").index
            tempTracer = self.posData.loc[idx[-2::]]
            self.tracer.set_data(tempTracer.x, tempTracer.y) #, color=self.color)
            self.tracer.set_3d_properties(tempTracer.z)
            # if time-self.startTime > (self.endTime-self.startTime)/2:
            #     self.line.set_color(self.color)
        
    

class TrajectoryAnimator():
    def __init__(self, particles:List[TrajectoryParticle], plotLimits=AU, dpi=96, dt=3600, speed=50) -> None:
        plt.style.use("dark_background")


        self.plotLimits = plotLimits

        self.dpi = dpi
        self.fig = plt.figure(figsize=(1920/dpi, 1080/dpi), dpi=dpi)
        
        self.ax = self.fig.add_subplot(111, projection="3d")

        self.ax.set_ylim(-plotLimits, plotLimits)
        self.ax.set_xlim(-plotLimits, plotLimits)
        self.ax.set_zlim(-plotLimits/2, plotLimits/2)
        self.ax.set_box_aspect((2, 2, 1), zoom=1.41)


        self.particles = particles
        
        endTime = -1000
        startTime = 1e20
        for particle in self.particles:
            particle.line = self.ax.plot([], [], [])[0] # type: ignore
            particle.tracer = self.ax.plot([], [], [])[0] # type: ignore

            particle._dropBySpeed(speed)
            
            startTime = min(startTime, particle.timeData.t.iloc[0])
            endTime = max(endTime, particle.timeData.t.iloc[-1])

        self.lines = [particle.line for particle in self.particles]

        self.timeData = np.arange(startTime, endTime, int(dt*speed))

        self.totalSteps = len(self.timeData)
        self.fig.tight_layout()
        plt.axis("off")


    def _animateFunction(self, i):
        self.ax.view_init(elev=15., azim=-130)
        for particle in self.particles:
            particle._updateLine(self.timeData[i])
        return self.lines
    
    def runAnimation(self, savefile="anim", fps=120):
        anim = FuncAnimation(self.fig, self._animateFunction, frames=tqdm(range(self.totalSteps)), interval=1, blit=True)

        if not os.path.exists("animations"):
            os.makedirs("animations")
        
        fullSaveName = "animations/" + savefile + ".mp4"
        print("Saving to " + fullSaveName)
        anim.save(fullSaveName, fps=fps, extra_args=["-vcodec", "libx264"], dpi=self.dpi)




if __name__ == "__main__":
    thing1 = TrajectoryParticle("object1", r"data/mass400_area12000.dat", "#d1495b")
    thing2 = TrajectoryParticle("object2", r"data/mass700_area10000.dat", "#26C485")

    traj = TrajectoryAnimator([thing1, thing2], speed=40)

    traj.runAnimation()