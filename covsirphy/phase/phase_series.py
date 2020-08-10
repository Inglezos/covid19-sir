#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta
import numpy as np
import pandas as pd
from covsirphy.cleaning.term import Term
from covsirphy.phase.phase_unit import PhaseUnit
from covsirphy.phase.sr_change import ChangeFinder


class PhaseSeries(Term):
    """
    A series of phases.

    Args:
        first_date (str): the first date of the series, like 22Jan2020
        last_date (str): the last date of the records, like 25May2020
        population (int): initial value of total population in the place
    """

    def __init__(self, first_date, last_date, population, name="Main"):
        self.first_date = self.ensure_date(first_date, "first_date")
        self.last_date = self.ensure_date(last_date, "last_date")
        self.init_population = self.ensure_population(population)
        # List of PhaseUnit
        self._units = []
        self.clear(include_past=True)

    def __str__(self):
        return f"{self.name} scenario"

    def __bool__(self):
        return self._units

    def __iter__(self):
        for unit in self._unit:
            yield unit
        raise StopIteration()

    def unit(self, phase="last"):
        """
        Return the unit of the phase.

        Args:
            phase (str): phase name (1st etc.) or "last"

        Returns:
            covsirphy.PhaseUnit: the unit of the phase

        Notes:
            When @phase is 'last' and no phases were registered, returns A phase
            with the start/end dates are the previous date of the first date and initial population value.
        """
        if phase == "last":
            if self._units:
                return self._units[-1]
            pre_date = self.yesterday(self.first_date)
            return PhaseUnit(pre_date, pre_date, self.init_population)
        num = self.str2num(phase)
        try:
            return self._units[num]
        except KeyError:
            raise KeyError(f"{phase} phase is not registered.")

    def clear(self, include_past=False):
        """
        Clear phase information. Future phases will be always deleted.

        Args:
            include_past (bool): if True, include past phases.

        Returns:
            covsirphy.PhaseSeries: self
        """
        if include_past:
            self._units = []
        self._units = [unit for unit in self._units if unit <= self.last_date]
        return self

    def _calc_end_date(self, start_date, end_date=None, days=None):
        """
        Return the end date.

        Args:
            start_date (str): start date of the phase
            end_date (str): end date of the past phase, like 22Jan2020
            days (int or None): the number of days to add

        Returns:
            str: end date
        """
        if end_date is not None:
            self.ensure_date_order(start_date, end_date, name="end_date")
            return end_date
        if days is None:
            return self.last_date
        days = self.ensure_natural_int(days, name="days", none_ok=False)
        end = self.date_obj(start_date) + timedelta(days=days)
        return end.strftime(self.DATE_FORMAT)

    def add(self, end_date=None, days=None, population=None, model=None, tau=None, **kwargs):
        """
        Add a past phase.

        Args:
            end_date (str): end date of the past phase, like 22Jan2020
            days (int or None): the number of days to add
            population (int or None): population value
            model (covsirphy.ModelBase): ODE model
            tau (int or None): tau value [min], a divisor of 1440 (prioritize the previous value)
            kwargs: keyword arguments of model parameters

        Returns:
            covsirphy.PhaseSeries: self

        Notes:
            If @population is None, the previous initial value will be used.
            When addition of past phases was not completed and the new phase is future phase, fill in the blank.
        """
        last_unit = self.unit(phase="last")
        # Basic information
        start_date = self.tomorrow(last_unit.end_date)
        end_date = self._calc_end_date(
            start_date, end_date=end_date, days=days)
        population = self.ensure_population(population or last_unit.population)
        model = model or last_unit.model
        tau = last_unit.tau or tau
        # Create PhaseUnit
        unit = PhaseUnit(start_date, end_date, population)
        unit.set_ode(model=model, tau=tau, **kwargs)
        # Add phase if past
        if unit <= self.last_date:
            self._units.append(unit)
            return self
        # Fill in the blank
        if last_unit < self.last_date:
            filling = PhaseUnit(start_date, self.last_date, population)
            filling.set_ode(model=model, tau=tau, **kwargs)
            self._units.append(filling)
            unit = PhaseUnit(
                self.tomorrow(self.last_date), end_date, population)
            unit.set_ode(model=model, tau=tau, **kwargs)
        # Add new phase
        self._units.append(unit)

    def delete(self, phase):
        """
        Delete a phase. The phase will be combined to the previous phase.

        Args:
            phase (str): phase name, like 0th, 1st, 2nd...

        Returns:
            covsirphy.PhaseSeries: self
        """
        if phase == "0th":
            self._units = self._units[1:]
            return self
        phase_pre = self.num2str(self.str2num(phase) - 1)
        unit_pre, unit = self.unit(phase_pre), self.unit(phase)
        unit_new = PhaseUnit(
            unit_pre.start_date, unit.end_date, unit_pre.population)
        model = unit_pre.model
        if unit_pre <= self.last_date or model is None:
            param_dict = {}
        else:
            param_dict = {
                k: v for (k, v) in unit_pre.to_dict().items() if k in model.PARAMETERS}
        unit_new.set_ode(model=model, tau=unit_pre.tau, **param_dict)
        units = [
            unit for unit in [unit_new, *self._units] if unit not in [unit_pre, unit]]
        self._units = sorted(units)

    def disable(self, phase):
        """
        The phase will be disabled and removed from summary.

        Args:
            phase (str): phase name, like 0th, 1st, 2nd...

        Returns:
            covsirphy.PhaseSeries: self
        """
        phase_id = self.str2num(phase)
        self._units[phase_id].disable()
        return self

    def enable(self, phase):
        """
        The phase will be enabled and appears in summary.

        Args:
            phase (str): phase name, like 0th, 1st, 2nd...

        Returns:
            covsirphy.PhaseSeries: self
        """
        phase_id = self.str2num(phase)
        self._units[phase_id].enable()
        return self

    def summary(self):
        """
        Summarize the series of phases in a dataframe.

        Returns:
            (pandas.DataFrame):
                Index:
                    - phase name, like 1st, 2nd, 3rd...
                Columns:
                    - Type: 'Past' or 'Future'
                    - Start: start date of the phase
                    - End: end date of the phase
                    - Population: population value of the start date
                    - other information registered to the phases
        """
        info_dict = self.to_dict()
        if not info_dict:
            return pd.DataFrame(columns=[self.TENSE, self.START, self.END, self.N])
        # Convert to dataframe
        df = pd.DataFrame.from_dict(info_dict, orient="index")
        return df.dropna(how="all", axis=1).fillna(self.UNKNOWN)

    def to_dict(self):
        """
        Summarize the series of phase in a dictionary.

        Returns:
            (dict): nested dictionary of phase information
                - key (str): phase number, like 1th, 2nd,...
                - value (dict): phase information
                    - 'Type': (str) 'Past' or 'Future'
                    - values of PhaseUnit.to_dict()
        """
        return {
            self.num2str(phase_id): {
                self.TENSE: self.PAST if unit <= self.last_date else self.FUTURE,
                **unit.to_dict()
            }
            for (phase_id, unit) in enumerate(self._units) if unit
        }

    def replace(self, phase, new):
        """
        Replace phase object.

        Args:
            phase (str): phase name, like 0th, 1st, 2nd...
            new (covsirphy.PhaseUnit): new phase object
        """
        old = self.unit(phase)
        if old != new:
            raise ValueError(
                "Combination of start/end date is different. old: {old}, new: {new}")
        units = [unit for unit in [new, *self._unit] if unit != old]
        self._units = sorted(units)

    def replaces(self, phase, new_list):
        """
        Replace phase object.

        Args:
            phase (str): phase name, like 0th, 1st, 2nd...
            new_list (list[covsirphy.PhaseUnit]): new phase objects
        """
        old = self.unit(phase)
        type_ok = all(isinstance(unit, PhaseUnit) for unit in new_list)
        if not isinstance(new_list, list) or len(new_list) < 2 or not type_ok:
            raise TypeError(
                "@new_list must be a list of covsirphy.PhaseUnit and length must be 2 or over.")
        units = [unit for unit in self._units if unit != old]
        self._units = sorted(units + new_list)

    def trend(self, sr_df, set_phases=True, area=None, show_figure=True, filename=None, **kwargs):
        """
        Perform S-R trend analysis.

        Args:
            sr_df (pandas.DataFrame)
                Index:
                    Date (pd.TimeStamp): Observation date
                Columns:
                    - Recovered (int): the number of recovered cases (> 0)
                    - Susceptible (int): the number of susceptible cases
                    - any other columns will be ignored
            set_phases (bool): if True, update phases
            area (str or None): area name
            show_figure (bool): if True, show the result as a figure
            filename (str): filename of the figure, or None (show figure)
            kwargs: keyword arguments of ChangeFinder()

        Returns:
            covsirphy.PhaseSeries: self
        """
        area = area or self.UNKNOWN
        sta = self.date_obj(self.first_date)
        end = self.date_obj(self.last_date)
        sr_df = sr_df.loc[(sr_df.index >= sta) & (sr_df.index <= end), :]
        finder = ChangeFinder(sr_df, **kwargs)
        if not set_phases:
            if show_figure:
                change_dates = [
                    unit.start_date for unit in self._units[1:] if unit < self.last_date]
                finder.show(
                    area=area, change_dates=change_dates, filename=filename)
            return self
        # Find change points
        finder.run()
        # Show trends
        if show_figure:
            finder.show(area=area, filename=filename)
        # Register phases
        self.clear(include_past=True)
        _, end_dates = finder.date_range()
        [self.add(end_date=end_date) for end_date in end_dates]
        self.disable("0th")
        return self

    def simulate(self, record_df, y0_dict=None):
        """
        Simulate ODE models with set parameter values.

        Args:
            record_df (pandas.DataFrame):
                Index:
                    reset index
                Columns:
                    - Date (pd.TimeStamp): Observation date
                    - Confirmed (int): the number of confirmed cases
                    - Infected (int): the number of currently infected cases
                    - Fatal (int): the number of fatal cases
                    - Recovered (int): the number of recovered cases (> 0)
                    - Susceptible (int): the number of susceptible cases
            y0_dict (dict or None):
                - key (str): variable name
                - value (float): initial value
                - dictionary of initial values or None
                - if model will be changed in the later phase, must be specified

        Returns:
            (pandas.DataFrame)
                Index:
                    reset index
                Columns:
                    - Date (pd.TimeStamp): Observation date
                    - Country (str): country/region name
                    - Province (str): province/prefecture/state name
                    - variables of the models (int): Confirmed (int) etc.
        """
        dataframes = []
        for unit in self._units:
            try:
                unit.set_y0(dataframes[-1])
            except IndexError:
                unit.set_y0(record_df)
            df = unit.simulate(y0_dict)
            dataframes.append(df)
        sim_df = pd.concat(dataframes, ignore_index=True, sort=True)
        sim_df = sim_df.set_index(self.DATE).resample("D").last()
        sim_df = sim_df.astype(np.int64)
        return sim_df.reset_index()
