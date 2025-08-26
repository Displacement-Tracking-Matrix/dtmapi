<p align="center">
  <img alt="DTM Logo" src="https://dtm.iom.int/themes/custom/dtm_global/logo.svg" width="400">
</p>

---

# dtmapi

![PyPI](https://img.shields.io/pypi/v/dtmapi)
![Documentation Status](https://readthedocs.org/projects/dtmapi/badge/?version=latest)
![License](https://img.shields.io/github/license/Displacement-tracking-Matrix/dtmapi)

## About

`dtmapi` is a Python package developed by [Displacement Tracking Matrix (DTM)](https://dtm.iom.int/). This package allows the humanitarian community, academia, media, government, and non-governmental organizations to utilize the data collected by DTM. It provides non-sensitive Internally Displaced Person (IDP) figures, aggregated at the country, Admin 1 (states, provinces, or equivalent), and Admin 2 (smaller subnational administrative areas) levels.

Please find more information about [DTM API](https://dtm.iom.int/data-and-analysis/dtm-api) here.

---

## What's New in Version 3?

Version 3 of the DTM Displacement API introduces a range of new data indicators and improvements designed to enhance the analysis of internal displacement patterns. These enhancements aim to provide deeper insight into the dynamics of displacement by incorporating more granular and meaningful data points.

Key improvements include:

- **Origin of Displacement**  
   Identify the geographical origin or location where displacement began, offering better tracking of movement patterns.
- **Gender Disaggregation**  
  Access disaggregated data by gender to support more inclusive and targeted humanitarian responses.
- **Reason for Displacement**  
  Understand the primary causes of displacement, including conflict, disasters, and other drivers.

These new indicators help improve planning, policy-making, and response strategies for stakeholders working with displacement data.

---

## How to Get a subscription API Key

Access to the DTM API now requires a personal API subscription key.

1. Go to the **DTM API Registration Portal**:  
   [https://dtm-apim-portal.iom.int/](https://dtm-apim-portal.iom.int/)

2. Sign up or log in with personal details such as name, email, job title, and organization.

3. In the **APIs** section, select **API-V3**.

4. Click **Subscribe**.  
   A subscription name is requested - choose a meaningful name for identification.

5. Once the subscription is activated, the API key can be accessed under the **Profile** section in the top menu bar.

   - The **Primary key** shown there serves as the personal API KEY.
   - The available endpoints for this API version are also listed.

6. The API key should be copied and stored securely. It is required for authenticating all requests when using the `dtmapi` Python package.

---

## Installation

`dtmapi` is available on [PyPI](https://pypi.org/project/dtmapi/). It can be installed as below:

```sh
pip install dtmapi
```

## Usage

Here's a quick example to get you started:

```python
from dtmapi import DTMApi

# Instantiate the API client with your subscription key.
api = DTMApi(subscription_key="YOUR-API-KEY-HERE")
```

```python
# Get all countries for which DTM data is publicly available through the API.
all_country_list = api.get_all_countries()
all_country_list.head()

# Get all operations for which DTM data is publicly available through the API.
all_operation_list = api.get_all_operations()
all_operation_list.head()

# Get IDP Admin 0 Data for Ethiopia from Round 1 to Round 10.
idp_admin0_data = api.get_idp_admin0_data(CountryName='Ethiopia', FromRoundNumber=1, ToRoundNumber=10)
idp_admin0_data.head()

# Get IDP Admin 1 Data for Sudan from reporting date 2020-01-01 to 2024-08-15.
idp_admin1_data = api.get_idp_admin1_data(CountryName='Sudan', Admin1Name="Blue Nile",
                                          FromReportingDate='2020-01-01', ToReportingDate='2024-08-15')
idp_admin1_data.head()

# Get IDP Admin 2 Data for Lebanon.
idp_admin2_data = api.get_idp_admin2_data(Operation="Displacement due to conflict", CountryName='Lebanon')
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

For any questions or feedback, please reach out to us at [dtmdataconsolidation@iom.int](mailto:dtmdataconsolidation@iom.int).
