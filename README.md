<picture align="center">
  <source media="(prefers-color-scheme: dark)" srcset="https://dtm.iom.int/themes/custom/dtm_global/logo.svg">
  <img alt="DTM Logo" src="https://dtm.iom.int/themes/custom/dtm_global/logo.svg">
</picture>

-----------------

# dtmapi
![PyPI](https://img.shields.io/pypi/v/dtmapi)
![Documentation Status](https://readthedocs.org/projects/dtmapi/badge/?version=latest)
![License](https://img.shields.io/github/license/Displacement-tracking-Matrix/dtmapi)

## About
`dtmapi` is a Python package developed by Displacement Tracking Matrix (DTM). This package allows the humanitarian community, academia, media, government, and non-governmental organizations to utilize the data collected by DTM. It provides non-sensitive Internally Displaced Person (IDP) figures, aggregated at the country, Admin 1 (states, provinces, or equivalent), and Admin 2 (smaller subnational administrative areas) levels.

## Installation
`dtmapi` can be installed by using pip:
```sh
pip install dtmapi
```
## Usage
Here's a quick example to get you started:
```python
import dtmapi

# Get IDP Admin 0 Data for Ethiopia from Round 1 to Round 10
idp_admin0_data = dtmapi.get_idp_admin0_data(CountryName='Ethiopia', FromRoundNumber=1, ToRoundNumber=10, to_pandas=True)
idp_admin0_data.head()

# Get IDP Admin 1 Data for Sudan  from from reporting date 2020-01-01 to 2024-08-15
idp_admin1_data = dtmapi.get_idp_admin1_data(CountryName='Sudan', Admin1Name="Blue Nile", FromReportingDate='2020-01-01', ToReportingDate='2024-08-15', to_pandas=True)
idp_admin1_data.head()

# Get IDP Admin 2 Data for Lebanon
idp_admin2_data = dtmapi.get_idp_admin2_data(Operation="Displacement due to conflict", CountryName='Lebanon', to_pandas=True)
idp_admin2_data.head()
```

## Documentation
Comprehensive documentation is available at [dtmapi.readthedocs.io](https://dtmapi.readthedocs.io/en/latest/index.html).

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
## Contact
For any questions or feedback, please reach out to us at [dtmsupport@iom.int](mailto:dtmsupport@iom.int).