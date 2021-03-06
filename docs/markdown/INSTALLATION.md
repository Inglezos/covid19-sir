# Installation

The latest stable version of CovsirPhy is available at [PyPI (The Python Package Index): covsirphy](https://pypi.org/project/covsirphy/) and supports Python 3.7 or newer versions. It is recommended to use virtual environment.

```bash
pip install --upgrade covsirphy
```

You can find the latest development in [GitHub repository: CovsirPhy](https://github.com/lisphilar/covid19-sir) and install it with `pip` command. Please refer to [Guideline of contribution](https://lisphilar.github.io/covid19-sir/CONTRIBUTING.html).

```bash
pip install --upgrade "git+https://github.com/lisphilar/covid19-sir.git#egg=covsirphy"
```

# Dataset preparation

With `DataLoader` class, we can download recommended datasets for analysis and save/update them in your local environment. Optionally, you can use your local dataset which is saved in a CSV file.

All raw datasets are retrieved from public databases. No confidential information is included. If you find any issues, please let us know via [GitHub issue page](https://github.com/lisphilar/covid19-sir/issues).

## 1. Recommended datasets

With the following codes, we can download the latest recommended datasets and save them in "input" folder of the current directory. Please refer to [Usage (datasets)](https://lisphilar.github.io/covid19-sir/usage_dataset.html) to find the details of the datasets.

At first, import CovsirPhy package and check the version number.

```Python
import covsirphy as cs
cs.__version__
```

Save the recommended datasets in "input" folder of the current directory.  

```Python
# Create DataLoader instance
data_loader = cs.DataLoader("input")
# The number of cases (JHU style)
jhu_data = data_loader.jhu()
# Population in each country
population_data = data_loader.population()
# Government Response Tracker (OxCGRT)
oxcgrt_data = data_loader.oxcgrt()
```

```Python
# Linelist of case reports
linelist = data_loader.linelist()
# The number of tests
pcr_data = data_loader.pcr()
# The number of vaccinations
vaccine_data = data_loader.vaccine()
# Population pyramid
pyramid_data = data_loader.pyramid()
# Japan-specific dataset
japan_data = data_loader.japan()
```

The downloaded datasets were retrieved from the following sites.

### [COVID-19 Data Hub](https://covid19datahub.io/)

Guidotti, E., Ardia, D., (2020), "COVID-19 Data Hub", Journal of Open Source Software 5(51):2376, doi: 10.21105/joss.02376.

- The number of cases (JHU style)
- Population in each country
- [Government Response Tracker (OxCGRT)](https://github.com/OxCGRT/covid-policy-tracker)
- The number of tests

### [Open COVID-19 Data Working Group](https://github.com/beoutbreakprepared/nCoV2019)

Xu, B., Gutierrez, B., Mekaru, S. et al. Epidemiological data from the COVID-19 outbreak, real-time case information. Sci Data 7, 106 (2020). https://doi.org/10.1038/s41597-020-0448-0

- Linelist of case reports

### [Our World In Data](https://github.com/owid/covid-19-data/tree/master/public/data)

Hasell, J., Mathieu, E., Beltekian, D. et al. A cross-country database of COVID-19 testing. Sci Data 7, 345 (2020). [https://doi.org/10.1038/s41597-020-00688-8](https://doi.org/10.1038/s41597-020-00688-8)

- The number of tests
- The number of vaccinations
- The number of people who received vaccinations

### [World Bank Open Data](https://data.worldbank.org/)

World Bank Group (2020), World Bank Open Data, [https://data.worldbank.org/](https://data.worldbank.org/)

- Population pyramid

### [Datasets for CovsirPhy](https://github.com/lisphilar/covid19-sir/tree/master/data)

Lisphilar (2020), GitHub repository, COVID-19 dataset in Japan, [https://github.com/lisphilar/covid19-sir/tree/master/data](https://github.com/lisphilar/covid19-sir/tree/master/data).  

- The number of cases in Japan (total/prefectures)
- Metadata regarding Japan prefectures

## 2. How to request new data loader

If you want to use a new dataset for your analysis, please kindly inform us using [GitHub Issues: Request new method of DataLoader class](https://github.com/lisphilar/covid19-sir/issues/new/?template=request-new-method-of-dataloader-class.md). Please read [Guideline of contribution](https://lisphilar.github.io/covid19-sir/CONTRIBUTING.html) in advance.

## 3. Use a local CSV file which has the number of cases

We can replace `jhu_data` instance created by `DataLoader` class with your dataset saved in a CSV file. At this time, `covsirphy` supports country and province level data.

### 3.1. Create CountryData instance

Please create `CountryData` instance at first. Let's say we have a CSV file ("oslo.csv") with the following columns.

- "date": reported dates
- "confirmed": the number of confirmed cases
- "recovered": the number of recovered cases
- "fatal": the number of fatal cases
- "province": (optional) province names

Country level data will be set as total values of provinces with `CountryData.register_total()` method optionally.

```Python
# Create CountryData instance specifying filename and country name
country_data = cs.CountryData("oslo.csv", country="Norway")
# Specify column names
country_data.set_variables(
    date="date", confirmed="confirmed", recovered="recovered", fatal="fatal", province="province",
)
# (Optional) register total values of provinces as country level data
country_data.register_total()
# Check records -> pandas.DataFrame
# reset index, Date/Country/Province/Confirmed/Infected/Fatal/Recovered column
country_data.cleaned()
```

When we don't have province column and the all records are for one province, we can specify the province name as follows.

```Python
# Create CountryData instance specifying filename and country/province name
country_data = cs.CountryData("oslo.csv", country="Norway", province="Oslo")
# Specify column names except for province
country_data.set_variables(
    date="date", confirmed="confirmed", recovered="recovered", fatal="fatal",
)
# Check records
country_data.cleaned()
```

When we don't have province column and the all records are country level data, we can skip province name setting.

```Python
# Create CountryData instance specifying filename and country name
country_data = cs.CountryData("oslo.csv", country="Norway")
# Specify column names except for province
country_data.set_variables(
    date="date", confirmed="confirmed", recovered="recovered", fatal="fatal",
)
# Check records
country_data.cleaned()
```

### 3.2. Convert to JHUData instance

Then, convert the `CountryData` instance to a `JHUData` instance.

```Python
# Create JHUData instance using cleaned dataset (pandas.DataFrame)
jhu_data = cs.JHUData.from_dataframe(country_data.cleaned())
# Or, we can use and update the output of DataLoader.jhu()
# jhu_data = data_loader.jhu()
# jhu_data.replace(country_data)
```

### 3.3. Set population values

Additionally, you may need to register population values to `PopulationData` instance manually.

```Python
# Create PopulationData instance with empty dataset
population_data = cs.PopulationData()
# Or, we can use the output of DataLoader.population()
# population_data = data_loader.population()
# Update the population value: province is optional
population_data.update(693494, country="Norway", province="Oslo")
```

## 4. Data loading in Kaggle Notebook

We can use the recommended datasets in [Kaggle](https://www.kaggle.com/) Notebook. The datasets are saved in "/kaggle/input/" directory. Additionally, we can use Kaggle Datasets (CSV files) with `covsirphy` in Kaggle Notebook.

Note:  
If you have Kaggle API, you can download Kaggle datasets to your local environment by updating and executing [input.py](https://github.com/lisphilar/covid19-sir/blob/master/input.py) script. CSV files will be saved in "/kaggle/input/" directory.

Kaggle API:  
Move to account page of Kaggle and download "kaggle.json" by selecting "API > Create New API Token" button. Copy the json file to the top directory of the local repository or "~/.kaggle". Please refer to [How to Use Kaggle: Public API](https://www.kaggle.com/docs/api) and [stackoverflow: documentation for Kaggle API *within* python?](https://stackoverflow.com/questions/55934733/documentation-for-kaggle-api-within-python#:~:text=Here%20are%20the%20steps%20involved%20in%20using%20the%20Kaggle%20API%20from%20Python.&text=Go%20to%20your%20Kaggle%20account,json%20will%20be%20downloaded)

## 5. Acknowledgement

In Feb2020, CovsirPhy project started in Kaggle platform with [COVID-19 data with SIR model](https://www.kaggle.com/lisphilar/covid-19-data-with-sir-model) notebook using the following datasets.

- The number of cases (JHU) and linelist: [Novel Corona Virus 2019 Dataset by SRK](https://www.kaggle.com/sudalairajkumar/novel-corona-virus-2019-dataset)
- Population in each country:  [covid19 global forecasting: locations population by Dmitry A. Grechka](https://www.kaggle.com/dgrechka/covid19-global-forecasting-locations-population)
- The number of cases in Japan: [COVID-19 dataset in Japan by Lisphilar](https://www.kaggle.com/lisphilar/covid19-dataset-in-japan)

Best Regards.
