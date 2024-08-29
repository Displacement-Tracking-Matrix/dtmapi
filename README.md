<p align="center">
  <img alt="DTM Logo" src="https://dtm.iom.int/themes/custom/dtm_global/logo.svg" width="400">
</p>

-----------------

# dtmapi
![PyPI](https://img.shields.io/pypi/v/dtmapi)
![Documentation Status](https://readthedocs.org/projects/dtmapi/badge/?version=latest)
![License](https://img.shields.io/github/license/Displacement-tracking-Matrix/dtmapi)

## About
`dtmapi` is a Python package developed by [Displacement Tracking Matrix (DTM)](https://dtm.iom.int/). This package allows the humanitarian community, academia, media, government, and non-governmental organizations to utilize the data collected by DTM. It provides non-sensitive Internally Displaced Person (IDP) figures, aggregated at the country, Admin 1 (states, provinces, or equivalent), and Admin 2 (smaller subnational administrative areas) levels. Country Name and Operation can be found in this [data coverage](https://dtm.iom.int/data-and-analysis/dtm-api/data-coverage) matrix. 

## Installation
`dtmapi` is available on [PyPI](https://pypi.org/project/dtmapi/). It can be installed as below:
```sh
pip install dtmapi
```
## Usage
Here's a quick example to get you started:
```python
import dtmapi

# Get all countries for which DTM data is publicly available through the API.
all_country_list = dtmapi.get_all_country_list()
all_country_list.head()

# Get all operations for which DTM data is publicly available through the API.
all_operation_list = dtmapi.get_all_operation_list()
all_operation_list.head()

# Get IDP Admin 0 Data for Ethiopia from Round 1 to Round 10
idp_admin0_data = dtmapi.get_idp_admin0_data(CountryName='Ethiopia', FromRoundNumber=1, ToRoundNumber=10, to_pandas=True)
idp_admin0_data.head()

# Get IDP Admin 1 Data for Sudan from reporting date 2020-01-01 to 2024-08-15
idp_admin1_data = dtmapi.get_idp_admin1_data(CountryName='Sudan', Admin1Name="Blue Nile", FromReportingDate='2020-01-01', ToReportingDate='2024-08-15', to_pandas=True)
idp_admin1_data.head()

# Get IDP Admin 2 Data for Lebanon
idp_admin2_data = dtmapi.get_idp_admin2_data(Operation="Displacement due to conflict", CountryName='Lebanon', to_pandas=True)
idp_admin2_data.head()
```
## Documentation
Comprehensive documentation is available at [dtmapi.readthedocs.io](https://dtmapi.readthedocs.io/en/latest/index.html).

## Source Code
The source code for `dtmapi` is available on [GitHub](https://github.com/Displacement-tracking-Matrix/dtmapi).

Feel free to explore the repository, contribute, or raise any issues you may encounter.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
## Contact
For any questions or feedback, please reach out to us at [dtmsupport@iom.int](mailto:dtmsupport@iom.int).
