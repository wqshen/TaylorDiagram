import matplotlib.pyplot as plt
import numpy as np
from numpy.core.fromnumeric import shape
import pandas as pd
import dask.dataframe as dd
from matplotlib.projections import PolarAxes
import mpl_toolkits.axisartist.floating_axes as FA
import mpl_toolkits.axisartist.grid_finder as GF


class TaylorDiagram:
    """
    ref: pandas.DataFrame one column
    samples: pandas.DataFrame multiple columns
    """

    def __init__(self, ax, ref, samples, markers=[], colors=[], scale=1.2, ms=10, mkwargs={}):
        self.points = []
        self.mkwargs = mkwargs
        self.markers = markers if len(markers) else ['^', 'o', 's', 'v', 'o', 's', 'v']
        self.colors = colors if len(colors) else ['tab:blue', 'tab:red', 'tab:red', 'tab:red', 'tab:green', 'tab:green', 'tab:green']
        self.ms = ms
        self.ref = ref
        self.scale = scale
        self.samples = samples
        self.refstd = ref.std()
        self.fig = plt.gcf()  # get current figure
        self.step_up(ax)  # set up a diagram axes
        self.plot_sample()  # draw sample points
        # self.add_legend()  # add legend

    def calc_loc(self, x, y):
        # x为参考数据，y为评估数据
        # theta为弧度；r为半径
        R = x.corr(other=y, method='pearson')
        theta = np.arccos(R)
        r = y.std()
        return theta, r

    def step_up(self, ax):
        # close the original axis
        ax.axis('off')
        ll, bb, ww, hh = ax.get_position().bounds
        # polar transform
        tr = PolarAxes.PolarTransform()
        # theta range
        Rlocs = np.array([0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1])
        Tlocs = np.arccos(Rlocs)  # convrt to theta locations
        # grid finder
        gl1 = GF.FixedLocator(Tlocs)  # theta locator
        tf1 = GF.DictFormatter(dict(zip(Tlocs, map(str, Rlocs))))  # theta formatter
        # std range
        Smin = 0
        Smax = max([self.samples[col].std() for col in self.samples.columns] + [self.ref.std()]) * self.scale
        # construct grid helper
        grid_helper = FA.GridHelperCurveLinear(
            tr, extremes=(0, np.pi / 2, Smin, Smax),
            grid_locator1=gl1, tick_formatter1=tf1
        )
        ax = FA.FloatingSubplot(self.fig, 111, grid_helper=grid_helper)
        ax = self.fig.add_subplot(ax)
        ax.set_position([ll, bb, ww, hh])
        # Adjust axes
        # theta
        ax.axis["top"].set_axis_direction("bottom")
        ax.axis["top"].toggle(ticklabels=True, label=True)
        ax.axis["top"].major_ticklabels.set_axis_direction("top")
        ax.axis["top"].label.set_axis_direction("top")
        ax.axis["top"].label.set_text("Correlation")
        # std left
        ax.axis["left"].set_axis_direction("bottom")
        ax.axis["left"].label.set_text("Standard deviation")
        # std bottom
        ax.axis["right"].set_axis_direction("top")
        ax.axis["right"].toggle(ticklabels=True, label=True)
        ax.axis["right"].label.set_text("Standard deviation")
        ax.axis["right"].major_ticklabels.set_axis_direction("left")
        # hide
        ax.axis['bottom'].set_visible(False)
        # draw grid
        ax.grid(axis='x', linestyle='--', color='gray')
        self._ax = ax
        self.ax = ax.get_aux_axes(tr)
        # STD线
        t = np.linspace(0, np.pi/2)
        r = np.zeros_like(t) + self.refstd
        self.ax.plot(t, r, 'k--')
        # RMS格网
        rs, ts = np.meshgrid(np.linspace(Smin, Smax, 100), np.linspace(0, np.pi/2, 100))
        rms = np.sqrt(self.refstd**2 + rs**2 - 2*self.refstd*rs*np.cos(ts))
        contours = self.ax.contour(ts, rs, rms, levels=4,
                            colors='gray', linestyles='--', alpha=.5)
        self.ax.clabel(contours, contours.levels, inline=True, fmt='%.1f', fontsize=10)
        # 绘制参考点
        p, = self.ax.plot(0, self.refstd, linestyle='', marker=self.markers[0], color=self.colors[0], 
                          markersize=self.ms, alpha=0.5, **self.mkwargs)
        p.set_label(self.ref.name)
        self.points.append(p)

    def plot_sample(self):
        stds = []
        for col, marker, color in zip(self.samples.columns, self.markers[1:], self.colors[1:]):
            t, s = self.calc_loc(self.ref, self.samples[col])
            p, = self.ax.plot(t, s, linestyle='', marker=marker, color=color, 
                              markersize=self.ms, alpha=.5, **self.mkwargs)
            p.set_label(col)
            self.points.append(p)
            stds.append(s)
        self.ax.set_xlim(xmax=max(stds))

    def add_legend(self):
        ll, bb, ww, hh = self.ax.get_position().bounds
        self.ax.legend(ncol=len(self.samples) + 1, 
                       loc='lower center', 
                       frameon=False, 
                       bbox_to_anchor=(ll, bb - hh*0.3, ww, hh*0.1))

if __name__ == "__main__":
    print('read data')
    df = dd.read_csv(
        'F:/MeteorologicalData/point-grid/station-6satellite-pure-BeijingTime-New.csv').head(100000000)
    print(df)
    fig, axes = plt.subplots(1, 3, figsize=(12, 6))
    td = TaylorDiagram(axes[0], df.iloc[:, 5], df.iloc[:, 6:], ms=8)
    plt.show()