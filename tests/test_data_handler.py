#!/usr/bin/env python
# -*- coding: utf-8 -*-

from covsirphy.util.error import SubsetNotFoundError
import pytest
from covsirphy import DataHandler, JHUData, PopulationData, Term
from covsirphy import CountryData, JapanData, OxCGRTData, PCRData, VaccineData
from covsirphy import UnExpectedValueError, NotRegisteredMainError, NotRegisteredExtraError


class TestDataHandler(object):
    @pytest.mark.parametrize("country", ["Japan"])
    def test_register(self, data, country):
        dhl = DataHandler(country=country, province=None)
        # Main datasets
        if isinstance(data, JHUData):
            return dhl.register(jhu_data=data)
        if isinstance(data, PopulationData):
            return dhl.register(population_data=data)
        # Extra datasets
        if isinstance(data, [CountryData, JapanData, OxCGRTData, PCRData, VaccineData]):
            return dhl.register(extras=[data])
        # Un-acceptable datasets
        with pytest.raises(UnExpectedValueError):
            dhl.register(extras=[data])

    @pytest.mark.parametrize("country", ["Moon"])
    def test_register_unknown_area(self, jhu_data, population_data, country):
        dhl = DataHandler(country=country, province=None)
        dhl.register(jhu_data=jhu_data)
        with pytest.raises(SubsetNotFoundError):
            dhl.register(population_data=population_data)

    @pytest.mark.parametrize("country", ["Japan"])
    def test_population(self, jhu_data, population_data, country):
        dhl = DataHandler(country=country, province=None)
        assert not dhl.main_satisfied
        with pytest.raises(NotRegisteredMainError):
            assert dhl.population == population_data.value(country=country)
        dhl.register(jhu_data=jhu_data, population_data=population_data)
        assert dhl.main_satisfied
        assert dhl.population == population_data.value(country=country)

    @pytest.mark.parametrize("country", ["Japan"])
    def test_complement(self, jhu_data, population_data, country):
        dhl = DataHandler(country=country, province=None)
        with pytest.raises(NotRegisteredMainError):
            assert dhl.complemented is None
        with pytest.raises(NotRegisteredMainError):
            dhl.show_complement()
        dhl.register(jhu_data=jhu_data, population_data=population_data)
        # Not complemented
        dhl.switch_complement(whether=False)
        dhl.records_main()
        dhl.show_complement()
        assert not dhl.complemented
        # Complemented
        dhl.switch_complement(whether=True)
        dhl.records_main()
        dhl.show_complement()
        assert dhl.complemented

    @pytest.mark.parametrize("country", ["Japan"])
    def test_recovery_period(self, jhu_data, country):
        dhl = DataHandler(country=country, province=None)
        with pytest.raises(NotRegisteredMainError):
            assert isinstance(dhl.recovery_period(), int)
        dhl.register(jhu_data=jhu_data)
        assert isinstance(dhl.recovery_period(), int)

    @pytest.mark.parametrize("country", ["Japan"])
    def test_records_main(self, jhu_data, population_data, country):
        dhl = DataHandler(country=country, province=None)
        with pytest.raises(NotRegisteredMainError):
            dhl.records_main()
        dhl.register(jhu_data=jhu_data, population_data=population_data)
        assert dhl.population == population_data.value(country=country)

    @pytest.mark.parametrize("country", ["Japan"])
    def test_timepoints(self, jhu_data, population_data, country):
        dhl = DataHandler(
            country=country, province=None, jhu_data=jhu_data, population_data=population_data)
        dhl.timepoints(first_date="01Apr2020", last_date="01Sep2020", today="01Jun2020")
        series = dhl.records_main()[Term.DATE]
        assert series.min().strftime(Term.DATE_FORMAT) == dhl.first_date == "01Apr2020"
        assert series.max().strftime(Term.DATE_FORMAT) == dhl.last_date == "01Sep2020"
        assert dhl.today == "01Jun2020"

    @pytest.mark.parametrize("country", ["Japan", "France"])
    def test_records_extras(self, jhu_data, population_data, country,
                            japan_data, oxcgrt_data, pcr_data, vaccine_data):
        dhl = DataHandler(country=country, province=None)
        with pytest.raises(NotRegisteredMainError):
            dhl.records_extras()
        dhl.register(jhu_data=jhu_data, population_data=population_data)
        dhl.timepoints(first_date="01Apr2020", last_date="01Sep2020")
        with pytest.raises(NotRegisteredExtraError):
            dhl.records_extras()
        dhl.register(extras=[japan_data, oxcgrt_data, pcr_data, vaccine_data])
        series = dhl.records_extras()[Term.DATE]
        assert series.min().strftime(Term.DATE_FORMAT) == dhl.first_date == "01Apr2020"
        assert series.max().strftime(Term.DATE_FORMAT) == dhl.last_date == "01Sep2020"

    @pytest.mark.parametrize("country", ["Japan"])
    @pytest.mark.parametrize("main", [True, False])
    @pytest.mark.parametrize("extras", [True, False])
    @pytest.mark.parametrize("past", [True, False])
    @pytest.mark.parametrize("future", [True, False])
    def test_records(self, jhu_data, population_data, country,
                     japan_data, oxcgrt_data, pcr_data, vaccine_data,
                     main, extras, past, future):
        dhl = DataHandler(country=country, province=None)
        # Combination of arguments
        if (not main and not extras) or (not past and not future):
            with pytest.raises(ValueError):
                dhl.records(main=main, extras=extras, past=past, future=future)
            return
        # Register main datasets
        if main:
            with pytest.raises(NotRegisteredMainError):
                dhl.records(main=main, extras=extras, past=past, future=future)
        dhl.register(jhu_data=jhu_data, population_data=population_data)
        dhl.timepoints(first_date="01Apr2020", last_date="01Sep2020", today="01Jun2020")
        # Register extra datasets
        if extras:
            with pytest.raises(NotRegisteredExtraError):
                dhl.records(main=main, extras=extras, past=past, future=future)
        dhl.register(extras=[japan_data, oxcgrt_data, pcr_data, vaccine_data])
        # Get records
        df = dhl.records(main=main, extras=extras, past=past, future=future)
        # Check the start/end date of the records
        if past and future:
            sta, end = "01Apr2020", "01Sep2020"
        elif past:
            sta, end = "01Apr2020", "01Jun2020"
        else:
            sta, end = "02Jun2020", "01Sep2020"
        assert df[Term.DATE].min().strftime(Term.DATE_FORMAT) == sta
        assert df[Term.DATE].max().strftime(Term.DATE_FORMAT) == end
