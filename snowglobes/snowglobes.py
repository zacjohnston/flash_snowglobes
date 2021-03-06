import numpy as np
import matplotlib.pyplot as plt

# snowglobes
from . import snow_tools
from . import snow_plot
from . import plot_tools
from . import config
from .slider import SnowSlider


class SnowGlobesData:
    def __init__(self,
                 model_sets=('LMP', 'LMP+N50', 'SNA'),
                 tabs=(1, 2, 3),
                 detector='ar40kt',
                 mass_list=None,
                 load_data=True,
                 output_dir='mass_tables_nomix',
                 n_bins=20,
                 ):
        """Collection of SnowGlobes data

        parameters
        ----------
        model_sets : [str]
            Labels for model sets
        tabs : [int]
            filename IDs that correspond to the model_sets
        detector : str
            Type of neutrino detector used in snowglobes
        mass_list : [float]
            progenitor ZAMS masses of models
        load_data : bool
            immediately load all data
        output_dir : str
            name of directory containing snowglobes data
        n_bins : int
            number of timebins to integrate over
        """
        self.detector = detector
        self.model_sets = model_sets
        self.tabs = tabs
        self.output_dir = output_dir
        self.n_bins = n_bins
        self.channels = config.channels[detector]
        self.mass_list = mass_list

        self.summary_tables = None
        self.mass_tables = None
        self.prog_table = None
        self.channel_fracs = None
        self.cumulative = None

        if self.mass_list is None:
            self.mass_list = config.mass_list

        self.n_mass = len(self.mass_list)

        if load_data:
            self.load_mass_tables()
            self.integrate_summary()
            self.load_prog_table()
            self.get_channel_fractions()

    # ===============================================================
    #                      Load Tables
    # ===============================================================
    def load_summary_tables(self):
        """Load all time-integrated summary tables
        """
        print('Loading summary tables')
        tables = dict.fromkeys(self.model_sets)

        for i, tab in enumerate(self.tabs):
            model_set = self.model_sets[i]
            tables[model_set] = snow_tools.load_summary_table(tab=tab,
                                                              detector=self.detector)
        self.summary_tables = tables

    def load_mass_tables(self):
        """Load time-dependent tables for all individual mass models
        """
        tables = dict.fromkeys(self.model_sets)

        for i, tab in enumerate(self.tabs):
            model_set = self.model_sets[i]
            print(f'Loading {model_set}')
            tables[model_set] = snow_tools.load_all_mass_tables(
                mass_list=self.mass_list,
                tab=tab,
                detector=self.detector,
                output_dir=self.output_dir)
        self.mass_tables = tables

    def load_prog_table(self):
        """Load progenitor table
        """
        prog_table = snow_tools.load_prog_table()
        self.prog_table = prog_table[prog_table['mass'].isin(self.mass_list)]

    # ===============================================================
    #                      Analysis
    # ===============================================================
    def integrate_summary(self, n_bins=None):
        """Integrate models over timebins
        """
        if n_bins is None:
            n_bins = self.n_bins

        self.print_time_slice(n_bins=n_bins)

        tables = {}
        for model_set in self.model_sets:
            print(f'Integrating: {model_set}')
            mass_tables = self.mass_tables[model_set]
            tables[model_set] = snow_tools.time_integrate(mass_tables=mass_tables,
                                                          n_bins=n_bins,
                                                          channels=self.channels)
        print()
        self.summary_tables = tables

    def get_cumulative(self, max_n_bins=None):
        """Integrate models over timebins
        """
        if max_n_bins is None:
            max_n_bins = self.n_bins

        self.print_time_slice(n_bins=max_n_bins - 1)
        tables = {}

        for model_set in self.model_sets:
            print(f'Integrating: {model_set}')
            mass_tables = self.mass_tables[model_set]
            tables[model_set] = snow_tools.get_cumulative(mass_tables=mass_tables,
                                                          max_n_bins=max_n_bins,
                                                          channels=self.channels)
        print()
        self.cumulative = tables

    def get_channel_fractions(self):
        """Calculate fractional contribution of each channel to total counts
        """
        self.channel_fracs = snow_tools.get_channel_fractions(tables=self.summary_tables,
                                                              channels=self.channels)

    # ===============================================================
    #                      Plotting
    # ===============================================================
    def plot_summary(self, y_var,
                     channel='Total',
                     x_var='m_fe',
                     marker='.',
                     x_scale=None,
                     y_scale=None,
                     x_lims=None,
                     y_lims=None,
                     legend=True,
                     legend_loc=None,
                     figsize=None,
                     ax=None,
                     data_only=False):
        """Plot quantity from summary table

        parameters
        ----------
        y_var : 'Tot' or 'Avg'
        channel : str
        x_var : str
        marker : str
        y_scale : str
        x_scale : str
        x_lims : [low, high]
        y_lims : [low, high]
        legend : bool
        legend_loc : int or str
        figsize : (width, length)
        ax : Axis
        data_only : bool
        """
        fig, ax = snow_plot.setup_fig_ax(ax=ax, figsize=figsize)

        for model_set, summary in self.summary_tables.items():
            snow_plot.plot_summary(summary=summary,
                                   y_var=y_var,
                                   channel=channel,
                                   x_var=x_var,
                                   prog_table=self.prog_table,
                                   marker=marker,
                                   ax=ax,
                                   label=model_set,
                                   color=config.colors.get(model_set),
                                   data_only=True)

        if not data_only:
            plot_tools.set_ax_all(ax=ax,
                                  x_var=x_var,
                                  y_var=y_var,
                                  x_scale=x_scale,
                                  y_scale=y_scale,
                                  x_lims=x_lims,
                                  y_lims=y_lims,
                                  legend=legend,
                                  legend_loc=legend_loc)
        return fig

    def plot_channels(self, y_var,
                      channels=None,
                      x_var='m_fe',
                      marker='.',
                      x_scale=None,
                      y_scale=None,
                      x_lims=None,
                      y_lims=None,
                      legend=True,
                      legend_loc=None,
                      figsize=None,
                      axes=None,
                      data_only=False,
                      ):
        """Plot summary variable for all channels

        parameters
        ----------
        y_var : 'Tot' or 'Avg'
        channels : [str]
        x_var : str
        marker : str
        y_scale : str
        x_scale : str
        x_lims : [low, high]
        y_lims : [low, high]
        legend : bool
        legend_loc : str or int
        figsize : (width, length)
        axes : [Axis]
        data_only : bool
        """
        if channels is None:
            channels = self.channels

        fig = None
        if axes is None:
            fig, axes = plt.subplots(len(channels), figsize=figsize, sharex=True)

        for model_set, summary in self.summary_tables.items():
            snow_plot.plot_channels(summary=summary,
                                    y_var=y_var,
                                    channels=channels,
                                    x_var=x_var,
                                    prog_table=self.prog_table,
                                    marker=marker,
                                    figsize=figsize,
                                    label=model_set,
                                    color=config.colors.get(model_set),
                                    legend=False,
                                    axes=axes,
                                    data_only=True)

        if not data_only:
            for i, channel in enumerate(channels):
                plot_tools.set_ax_all(ax=axes[i],
                                      x_var=x_var,
                                      y_var=y_var,
                                      x_scale=x_scale,
                                      y_scale=y_scale,
                                      x_lims=x_lims,
                                      y_lims=y_lims,
                                      y_label=f'{y_var} ({channel})')
        if legend:
            axes[0].legend(loc=legend_loc)

        return fig

    def plot_difference(self, y_var, ref_model_set,
                        channel='Total',
                        x_var='m_fe',
                        marker='.',
                        x_scale=None,
                        y_scale=None,
                        x_lims=None,
                        y_lims=None,
                        legend=True,
                        figsize=None,
                        ax=None):
        """Plot differences relative to a given model_set

        parameters
        ----------
        y_var : 'Tot' or 'Avg'
        channel : str
        ref_model_set : str
                which model_set to use as the baseline for comparison
        x_var : str
        marker : str
        y_scale : str
        x_scale : str
        x_lims : [low, high]
        y_lims : [low, high]
        legend : bool
        figsize : (width, length)
        ax : Axis
        """
        fig = snow_plot.plot_difference(tables=self.summary_tables,
                                        y_var=y_var,
                                        channel=channel,
                                        ref_model_set=ref_model_set,
                                        x_var=x_var,
                                        prog_table=self.prog_table,
                                        x_scale=x_scale,
                                        y_scale=y_scale,
                                        x_lims=x_lims,
                                        y_lims=y_lims,
                                        marker=marker,
                                        figsize=figsize,
                                        legend=legend,
                                        ax=ax)
        return fig

    def plot_time(self, y_var, mass,
                  channel='Total',
                  x_scale=None,
                  y_scale=None,
                  ax=None,
                  legend=True,
                  data_only=False,
                  ):
        """Plot time-dependent quantity from mass tables

        parameters
        ----------
        y_var : 'Tot' or 'Avg'
        channel : str
        mass : float or int
        y_scale : str
        x_scale : str
        ax : Axis
        legend : bool
        data_only : bool
        """
        fig, ax = snow_plot.setup_fig_ax(ax=ax, figsize=None)

        for model_set, mass_table in self.mass_tables.items():
            snow_plot.plot_time(mass_table=mass_table,
                                y_var=y_var,
                                mass=mass,
                                label=model_set,
                                color=config.colors.get(model_set),
                                channel=channel,
                                ax=ax,
                                data_only=True)

        if not data_only:
            plot_tools.set_ax_all(ax=ax,
                                  x_var='Time',
                                  y_var=y_var,
                                  x_scale=x_scale,
                                  y_scale=y_scale,
                                  legend=legend)

        return fig

    def plot_cumulative(self, y_var, mass,
                        channel='Total',
                        x_scale=None,
                        y_scale=None,
                        ax=None,
                        legend=True,
                        linestyle=None,
                        data_only=False,
                        ):
        """Plot cumulative quantity versus time

        parameters
        ----------
        y_var : 'Tot' or 'Avg'
        channel : str
        mass : float or int
        y_scale : str
        x_scale : str
        ax : Axis
        legend : bool
        linestyle : str
        data_only : bool
        """
        if self.cumulative is None:
            print('Need to extract cumulative data!')
            self.get_cumulative()

        fig, ax = snow_plot.setup_fig_ax(ax=ax, figsize=None)

        for model_set, cumulative in self.cumulative.items():
            snow_plot.plot_cumulative(cumulative=cumulative,
                                      y_var=y_var,
                                      mass=mass,
                                      channel=channel,
                                      x_scale=x_scale,
                                      y_scale=y_scale,
                                      ax=ax,
                                      label=model_set,
                                      color=config.colors.get(model_set),
                                      linestyle=linestyle,
                                      data_only=True)

        if not data_only:
            plot_tools.set_ax_all(ax=ax,
                                  x_var='timebins [5 ms]',
                                  y_var=y_var,
                                  x_scale=x_scale,
                                  y_scale=y_scale,
                                  legend=legend)
        return fig

    # ===============================================================
    #                      Slider Plots
    # ===============================================================
    def plot_summary_slider(self, y_var,
                            channel='Total',
                            x_var='m_fe',
                            marker='.',
                            x_scale=None,
                            y_scale=None,
                            x_lims=None,
                            y_lims=None,
                            x_factor=None,
                            y_factor=None,
                            legend=True,
                            legend_loc=None,
                            figsize=None):
        """Plot interactive summary table

        parameters
        ----------
        y_var : 'Tot' or 'Avg'
        channel : str
        x_var : str
        marker : str
        y_scale : str
        x_scale : str
        x_lims : [low, high]
        y_lims : [low, high]
        x_factor : float
        y_factor : float
        legend : bool
        legend_loc : int or str
        figsize : (width, length)
        """

        def update_slider(n_bins):
            n_bins = int(n_bins)

            for i, model_set in enumerate(self.model_sets):
                data = self.cumulative[model_set].sel(n_bins=n_bins)

                slider.update_ax_y(y=data[y_col],
                                   y_var=y_col,
                                   model_set=model_set)

            slider.fig.canvas.draw_idle()

        # ----------------
        if self.cumulative is None:
            print('Need to extract cumulative data!')
            self.get_cumulative()

        y_col = snow_tools.y_column(y_var=y_var, channel=channel)

        slider = SnowSlider(y_vars=[y_col],
                            n_bins=np.arange(1, self.n_bins + 1),
                            model_sets=self.model_sets,
                            x_factor=x_factor,
                            y_factor=y_factor)

        self.plot_summary(y_var=y_var,
                          x_var=x_var,
                          channel=channel,
                          x_scale=x_scale,
                          y_scale=y_scale,
                          x_lims=x_lims,
                          y_lims=y_lims,
                          marker=marker,
                          figsize=figsize,
                          legend=legend,
                          legend_loc=legend_loc,
                          ax=slider.ax)

        slider.slider.on_changed(update_slider)

        return slider

    # ===============================================================
    #                      Misc.
    # ===============================================================
    def print_time_slice(self, n_bins):
        """Print time limits for given n_bins

        Parameters
        ----------
        n_bins : int
        """
        model_set = self.model_sets[0]
        mass = self.mass_list[0]
        ref_table = self.mass_tables[model_set].sel(mass=mass)

        t0 = ref_table.Time.values[0]
        t1 = ref_table.Time.values[n_bins]
        print(f'Using timebins from {t0:.2f} to {t1:.2f} s')
