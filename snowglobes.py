from . import snow_tools
from . import config


class SnowGlobesData:
    def __init__(self,
                 model_sets=('LMP', 'LMP+N50', 'SNA'),
                 alphas=(1, 2, 3),
                 detector='ar40kt',
                 load_data=True):
        """Collection of SnowGlobes data

        parameters
        ----------
        model_sets : [str]
            Labels for model sets
        alphas : [int]
            filename IDs that correspond to the model_sets
        detector : str
            Type of neutrino detector used in snowglobes
        """
        self.detector = detector
        self.model_sets = model_sets
        self.alphas = alphas
        self.mass_list = config.mass_list
        self.n_mass = len(self.mass_list)

        self.summary_tables = None
        self.mass_tables = None

        if load_data:
            self.load_summary_tables()
            self.load_mass_tables()

    # ===============================================================
    #                      Load Tables
    # ===============================================================
    def load_summary_tables(self):
        """Load all time-integrated summary tables
        """
        print('Loading summary tables')
        tables = dict.fromkeys(self.model_sets)

        for i, alpha in enumerate(self.alphas):
            model_set = self.model_sets[i]
            tables[model_set] = snow_tools.load_summary_table(alpha=alpha,
                                                              detector=self.detector)
        self.summary_tables = tables

    def load_mass_tables(self):
        """Load time-dependent tables for all individual mass models
        """
        tables = dict.fromkeys(self.model_sets, {})

        for i, alpha in enumerate(self.alphas):
            model_set = self.model_sets[i]

            for j, mass in enumerate(self.mass_list):
                print(f'\rLoading mass tables, {model_set}: {j+1}/{self.n_mass}', end='')

                table = snow_tools.load_mass_table(mass=mass,
                                                   alpha=alpha,
                                                   detector=self.detector)
                tables[model_set][mass] = table

            print()

        self.mass_tables = tables

