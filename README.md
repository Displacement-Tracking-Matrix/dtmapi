<p align="center">
  <img alt="DTM Logo" src="https://dtm.iom.int/themes/custom/dtm_global/logo.svg" width="400">
</p>

<p align="center">
  <strong>Official Python Package for the Displacement Tracking Matrix (DTM) API</strong>
</p>

---

# dtmapi

![PyPI](https://img.shields.io/pypi/v/dtmapi)
![License](https://img.shields.io/github/license/Displacement-tracking-Matrix/dtmapi)

## 📑 Table of Contents

- [About](#about)
- [What's New in Version 3?](#whats-new-in-version-3)
- [How to Get an API Key](#how-to-get-a-subscription-api-key)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Versions](#api-versions)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## About

`dtmapi` is a Python package developed by [Displacement Tracking Matrix (DTM)](https://dtm.iom.int/). This package allows the humanitarian community, academia, media, government, and non-governmental organizations to utilize the data collected by DTM. It provides non-sensitive Internally Displaced Person (IDP) figures, aggregated at the country, Admin 1 (states, provinces, or equivalent), and Admin 2 (smaller subnational administrative areas) levels.

Please find more information about [DTM API](https://dtm.iom.int/data-and-analysis/dtm-api) here.

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

## How to Get a Subscription API Key

> **⚠️ Important:** Access to the DTM API requires a personal API subscription key. Never share your API key or commit it to version control.

1. Go to the **DTM API Registration Portal**:
   [https://dtm-apim-portal.iom.int/](https://dtm-apim-portal.iom.int/)

2. Sign up or log in with personal details such as name, email, job title, and organization.

3. In the **APIs** section, select **API-V3**.

4. Click **Subscribe**.
   A subscription name is requested - choose a meaningful name for identification.

5. Once the subscription is activated, the API key can be accessed under the **Profile** section in the top menu bar.

   - The **Primary key** shown there serves as your personal API KEY.
   - The available endpoints for this API version are also listed.

6. Copy and store your API key securely. It is required for authenticating all requests.

> **💡 Tip:** Use environment variables to store your API key instead of hardcoding it in your scripts.

---

## Installation

`dtmapi` is available on [PyPI](https://pypi.org/project/dtmapi/). Install it using pip:

```sh
pip install dtmapi
```

---

## Quick Start

Here's a complete example to get you started:

```python
from dtmapi import DTMApi

# Initialize the API client with your subscription key
api = DTMApi(subscription_key="YOUR-API-KEY-HERE")

# Get all available countries
all_countries = api.get_all_countries()
all_countries.head()

# Get all operations
all_operations = api.get_all_operations()
all_operations.head()

# Get IDP Admin 0 (country-level) data for Ethiopia, rounds 1-10
idp_admin0_data = api.get_idp_admin0_data(
    CountryName='Ethiopia',
    FromRoundNumber=1,
    ToRoundNumber=10
)
idp_admin0_data.head()

# Get IDP Admin 1 (state/province-level) data with date filtering
idp_admin1_data = api.get_idp_admin1_data(
    CountryName='Sudan',
    Admin1Name="Blue Nile",
    FromReportingDate='2020-01-01',
    ToReportingDate='2024-08-15'
)
idp_admin1_data.head()

# Get IDP Admin 2 (district-level) data by operation
idp_admin2_data = api.get_idp_admin2_data(
    Operation="Displacement due to conflict",
    CountryName='Lebanon'
)
idp_admin2_data.head()
```

---

## API Versions

> **📌 Recommended:** Use **v3** for all new projects. It includes enhanced demographic data and displacement context.

The DTM API supports two versions: **v3 (current)** and **v2 (legacy)**. The package defaults to v3, which is recommended for all new projects.

### Version Differences

| Feature                       | v2 (Legacy)                          | v3 (Current)                         |
| ----------------------------- | ------------------------------------ | ------------------------------------ |
| IDP Admin 0, 1, 2 Data        | <span style="color: green;">✓</span> | <span style="color: green;">✓</span> |
| Country List                  | <span style="color: green;">✓</span> | <span style="color: green;">✓</span> |
| Operation List                | <span style="color: green;">✓</span> | <span style="color: green;">✓</span> |
| **Gender/Sex Disaggregation** | <span style="color: red;">✗</span>   | <span style="color: green;">✓</span> |
| **Origin of Displacement**    | <span style="color: red;">✗</span>   | <span style="color: green;">✓</span> |
| **Displacement Reason**       | <span style="color: red;">✗</span>   | <span style="color: green;">✓</span> |
| Status                        | Legacy                               | **Current**                          |

### Using API v3 (Default - Recommended)

API v3 includes enhanced demographic data (gender disaggregation) and displacement context (origin, reason). This is the default version.

```python
from dtmapi import DTMApi

# v3 is default - no need to specify api_version
api = DTMApi(subscription_key="YOUR-API-KEY-HERE")

# Or explicitly specify v3
api = DTMApi(subscription_key="YOUR-API-KEY-HERE", api_version="v3")

# Fetch data with demographic disaggregation
data = api.get_idp_admin0_data(CountryName="Ethiopia")
# Returns data WITH gender, origin, and reason fields
```

### Using API v2 (Legacy)

API v2 is available for historical data consistency or when you need to compare with older datasets. It does not include the demographic enhancements introduced in v3.

```python
from dtmapi import DTMApi

# Specify v2 for legacy data format
api_v2 = DTMApi(subscription_key="YOUR-API-KEY-HERE", api_version="v2")

# Fetch data in legacy format
data = api_v2.get_idp_admin0_data(CountryName="Ethiopia")
# Returns data WITHOUT demographic disaggregation (v2 format)
```

### Comparing Versions

You can use both versions in the same script for comparison:

```python
from dtmapi import DTMApi

# Create separate instances for each version
api_v3 = DTMApi(subscription_key="YOUR-KEY", api_version="v3")
api_v2 = DTMApi(subscription_key="YOUR-KEY", api_version="v2")

# Fetch same data from both versions
data_v3 = api_v3.get_idp_admin0_data(CountryName="Syria", FromRoundNumber=1, ToRoundNumber=5)
data_v2 = api_v2.get_idp_admin0_data(CountryName="Syria", FromRoundNumber=1, ToRoundNumber=5)

# Compare columns - v3 includes additional demographic fields
data_v3.columns.tolist()
data_v2.columns.tolist()
```

### When to Use Each Version

- **Use v3** (recommended):

  - For all new projects
  - When you need demographic disaggregation (gender)
  - When you need displacement context (origin, reason)
  - For the most current and complete data

- **Use v2** (legacy):
  - When maintaining existing code that depends on v2 data structure
  - For historical comparisons with pre-v3 datasets
  - When integrating with systems expecting v2 format

---

## Documentation

Comprehensive documentation is available at [dtmapi.readthedocs.io](https://dtmapi.readthedocs.io/en/latest/index.html).

---

## Contributing

We welcome contributions from the community! The source code for `dtmapi` is available on [GitHub](https://github.com/Displacement-tracking-Matrix/dtmapi).

Feel free to:

- Star the repository
- Report bugs or issues
- Suggest new features
- Submit pull requests

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contact

For any questions or feedback, please reach out to us at [dtmdataconsolidation@iom.int](mailto:dtmdataconsolidation@iom.int).
