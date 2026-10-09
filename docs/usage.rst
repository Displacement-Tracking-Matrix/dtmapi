Usage Guide
===========

This guide covers installation, the displacement (``DTMApi``) and Humanitarian Needs Assessment
(``DTMHnaApi``) clients, configuration, and error handling.

Installation
------------

Install ``dtmapi`` using pip:

.. code-block:: bash

    pip install dtmapi

``dtmapi`` requires Python 3.8 or later.

Basic Usage
-----------

Initialize API Client
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from dtmapi import DTMApi

   # Initialize with your subscription key (defaults to v3)
   api = DTMApi(subscription_key="YOUR-API-KEY-HERE")

.. note::
   Store your API key securely using environment variables instead of hardcoding:

   .. code-block:: python

      import os
      api = DTMApi(subscription_key=os.environ["DTMAPI_SUBSCRIPTION_KEY"])

Get Available Countries and Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get all countries with available DTM data
    countries = api.get_all_countries()
    countries.head()

    # Get all operations
    operations = api.get_all_operations()
    operations.head()

Retrieving IDP Data
-------------------

IDP Admin 0 Data (Country Level)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get country-level IDP data with filtering options:

.. code-block:: python

    # Get IDP data for Sudan, rounds 1-10
    admin0_data = api.get_idp_admin0_data(
        CountryName='Sudan',
        FromRoundNumber=1,
        ToRoundNumber=10
    )
    admin0_data.head()

    # Filter by date range
    admin0_data = api.get_idp_admin0_data(
        CountryName='Sudan',
        FromReportingDate='2020-01-01',
        ToReportingDate='2024-12-31'
    )

IDP Admin 1 Data (State/Province Level)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get state/province-level data for Sudan
    admin1_data = api.get_idp_admin1_data(
        CountryName='Sudan',
        FromReportingDate='2020-01-01',
        ToReportingDate='2024-08-15'
    )
    admin1_data.head()

IDP Admin 2 Data (District Level)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get district-level data for Sudan
    admin2_data = api.get_idp_admin2_data(
        CountryName='Sudan',
        FromRoundNumber=1,
        ToRoundNumber=5
    )
    admin2_data.head()

API Versioning
--------------

The displacement API supports two versions: **v3 (current)** and **v2 (legacy)**. The package defaults to v3.

Using API v3 (Default - Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

API v3 includes enhanced demographic data and displacement context:

.. code-block:: python

    from dtmapi import DTMApi

    # v3 is default (recommended for new projects)
    api = DTMApi(subscription_key="YOUR-API-KEY-HERE")

    # Or explicitly specify v3
    api = DTMApi(subscription_key="YOUR-API-KEY-HERE", api_version="v3")

    # Fetch data with demographic disaggregation
    data = api.get_idp_admin0_data(CountryName="Sudan")
    # Returns data WITH gender, origin, and reason fields

v3 Enhanced Features:

- **Gender Disaggregation**: ``numberMales``, ``numberFemales``
- **Origin of Displacement**: ``idpOriginAdmin1Name``, ``idpOriginAdmin1Pcode``
- **Displacement Reason**: ``displacementReason``

Using API v2 (Legacy)
~~~~~~~~~~~~~~~~~~~~~

API v2 is available for historical data consistency:

.. code-block:: python

    from dtmapi import DTMApi

    # Specify v2 for legacy data format
    api_v2 = DTMApi(subscription_key="YOUR-API-KEY-HERE", api_version="v2")

    # Fetch data in legacy format
    data = api_v2.get_idp_admin0_data(CountryName="Sudan")
    # Returns data WITHOUT demographic disaggregation (v2 format)

Comparing API Versions
~~~~~~~~~~~~~~~~~~~~~~~

Compare data from both versions:

.. code-block:: python

    from dtmapi import DTMApi

    # Create separate instances for each version
    api_v3 = DTMApi(subscription_key="YOUR-KEY", api_version="v3")
    api_v2 = DTMApi(subscription_key="YOUR-KEY", api_version="v2")

    # Fetch same data from both versions
    data_v3 = api_v3.get_idp_admin0_data(
        CountryName="Sudan",
        FromRoundNumber=1,
        ToRoundNumber=5
    )
    data_v2 = api_v2.get_idp_admin0_data(
        CountryName="Sudan",
        FromRoundNumber=1,
        ToRoundNumber=5
    )

    # Compare columns - v3 includes additional demographic fields
    print("v3 columns:", data_v3.columns.tolist())
    print("v2 columns:", data_v2.columns.tolist())

    # Find v3-only columns
    v3_only = set(data_v3.columns) - set(data_v2.columns)
    print("v3-only columns:", v3_only)
    # Output: {'numberMales', 'numberFemales', 'idpOriginAdmin1Name',
    #          'idpOriginAdmin1Pcode', 'displacementReason'}

Humanitarian Needs Assessment (HNA)
-----------------------------------

``DTMHnaApi`` provides access to the DTM Humanitarian Needs Assessment endpoints.

Initialize the HNA Client
~~~~~~~~~~~~~~~~~~~~~~~~~

The HNA API is a separate subscription with **its own key**; the displacement key does not work for it
(see :ref:`how to get an HNA key <hna-key>` below). When no key is passed, ``DTMHnaApi`` reads ``DTMHNA_SUBSCRIPTION_KEY``. It never
falls back to ``DTMAPI_SUBSCRIPTION_KEY``.

.. code-block:: python

    import os
    from dtmapi import DTMHnaApi

    hna = DTMHnaApi(subscription_key=os.environ["DTMHNA_SUBSCRIPTION_KEY"])

The client targets the production gateway by default. Pass ``environment="dev"`` to use the development
gateway. The HNA API is versioned separately from the displacement API, so ``api_version`` defaults to ``"v1"``.
``timeout``, ``max_retries``, and ``retry_delay`` work as described in `Advanced Configuration`_.

.. _hna-key:

.. note::
   To get an HNA key, follow the same registration steps in the `DTM API Registration Portal <https://dtm-apim-portal.iom.int/>`_,
   but subscribe to the **HNA** API instead of **API-V3**.

Countries and the Indicator Catalog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Countries with HNA data
    countries = hna.get_all_countries()

    # The indicator catalog: one row per indicator in the Admin 2 data, with
    # indicator_category, indicator_name, description, and data_type
    catalog = hna.get_hna_data_catalog()

The catalog describes the *columns* returned by the Admin 2 endpoint, so it can be used to select the
indicators of one category:

.. code-block:: python

    needs = catalog[catalog["indicator_category"] == "Priority Needs"]
    data = hna.get_all_hna_admin2_data(Admin0Pcode="NGA", Year=2023)
    data[["m3695_meta_adm2_name", *needs["indicator_name"]]]

Admin 2 Data
~~~~~~~~~~~~

``Admin0Pcode`` (ISO 3166-1 alpha-3 country code) and ``Year`` are both required. The endpoint is paginated;
``get_all_hna_admin2_data`` requests every page and combines them:

.. code-block:: python

    data = hna.get_all_hna_admin2_data(Admin0Pcode="NGA", Year=2022)

    # Filter by population group: a string, a comma-separated string, or a list
    idps = hna.get_all_hna_admin2_data(
        Admin0Pcode="NGA",
        Year=2022,
        PopulationGroup=["IDP", "IDP returnee"],
    )

``max_pages`` (default: 100) caps the number of pages requested; a warning is logged if the cap is reached.
To handle paging yourself, ``get_hna_admin2_data`` returns a single page:

.. code-block:: python

    first_page = hna.get_hna_admin2_data(Admin0Pcode="NGA", Year=2022, Page=1)

Downloading the Excel Export
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The API prepares an ``.xlsx`` export and returns a short-lived download link (valid for about ten minutes).
``download_hna_data`` does both steps:

.. code-block:: python

    import pandas as pd

    # Save to a directory (the API's file name is used) or to an explicit path
    path = hna.download_hna_data(Admin0Pcode="NGA", Year=2022, file_path=".")
    df = pd.read_excel(path)

    # Without file_path, the file contents are returned as bytes
    content = hna.download_hna_data(Admin0Pcode="NGA", Year=2022)

To get the link itself, for example to open it in a browser, use ``get_hna_download_url``:

.. code-block:: python

    info = hna.get_hna_download_url(Admin0Pcode="NGA", Year=2022)
    info["downloadUrl"]  # link to the file
    info["fileName"]     # e.g. "Report_NGA_2022__20260914101710.xlsx"
    info["expiresAt"]    # expiry timestamp as returned by the API
    info.get("expires_at")  # the same, as a timezone-aware datetime (None if unparseable)

The subscription key is not sent to the download host; the link carries its own access token.

Advanced Configuration
----------------------

Customize Timeout and Retry Settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from dtmapi import DTMApi

    # Initialize with custom settings
    api = DTMApi(
        subscription_key="YOUR-API-KEY-HERE",
        api_version="v3",
        timeout=60,        # 60-second timeout (default: 30)
        max_retries=5,     # Retry up to 5 times (default: 3)
        retry_delay=2.0    # 2-second base delay between retries (default: 1)
    )

The retry logic uses exponential backoff and automatically retries on:

- HTTP 429 (Too Many Requests)
- HTTP 500, 502, 503, 504 (Server errors)
- Timeout errors
- Connection errors

Authentication failures (HTTP 401/403) are not retried.

Error Handling
--------------

The package provides custom exceptions for different error scenarios:

Exception Types
~~~~~~~~~~~~~~~

.. code-block:: python

    from dtmapi import (
        DTMApiError,              # Base exception
        DTMAuthenticationError,   # Authentication failures
        DTMApiResponseError,      # API error responses
        DTMApiRequestError,       # Request failures
        DTMApiTimeoutError,       # Timeout errors
        DTMApiVersionError,       # Invalid API version
        ValidationError           # Parameter validation errors (a ValueError, not a DTMApiError)
    )

``DTMHnaApi`` raises its own variants, so an error names the service that failed:

.. code-block:: python

    from dtmapi import (
        HNAError,          # Base exception for HNA errors
        HNAAuthError,      # also a DTMAuthenticationError
        HNAResponseError,  # also a DTMApiResponseError
        HNARequestError,   # also a DTMApiRequestError
        HNATimeoutError,   # also a DTMApiTimeoutError
        HNAVersionError,   # also a DTMApiVersionError (invalid version or environment)
    )

Each HNA exception also subclasses its ``DTMApi`` counterpart and ``DTMApiError``, so a single
``except DTMApiError`` handles API failures from both clients. Invalid parameters raise
``ValidationError``, a subclass of ``ValueError``, which must be caught separately.

Handling Validation Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from dtmapi import DTMApi, ValidationError

    api = DTMApi(subscription_key="YOUR-API-KEY-HERE")

    try:
        # Invalid date format
        data = api.get_idp_admin0_data(
            CountryName='Sudan',
            FromReportingDate='01-01-2024'  # Wrong format
        )
    except ValidationError as e:
        print(f"Validation Error: {e}")
        # Output: FromReportingDate must be in YYYY-MM-DD format, got: 01-01-2024

    try:
        # Invalid date range
        data = api.get_idp_admin0_data(
            CountryName='Sudan',
            FromReportingDate='2024-12-31',
            ToReportingDate='2024-01-01'  # End before start
        )
    except ValidationError as e:
        print(f"Validation Error: {e}")
        # Output: FromReportingDate (2024-12-31) must be before or equal to
        #         ToReportingDate (2024-01-01)

    try:
        # Missing required parameters
        data = api.get_idp_admin0_data()  # No filters provided
    except ValidationError as e:
        print(f"Validation Error: {e}")
        # Output: At least one of the following parameters is required:
        #         Operation, CountryName, Admin0Pcode

Handling API Errors
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from dtmapi import DTMApi, DTMAuthenticationError, DTMApiResponseError

    try:
        api = DTMApi(subscription_key="INVALID-KEY")
        data = api.get_all_countries()
    except DTMAuthenticationError as e:
        print(f"Authentication failed: {e}")
    except DTMApiResponseError as e:
        print(f"API error: {e}")
        print(f"Error messages: {e.error_messages}")

Logging
-------

Enable Logging for Debugging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The package uses Python's standard logging module:

.. code-block:: python

    import logging
    from dtmapi import DTMApi

    # Enable debug logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    api = DTMApi(subscription_key="YOUR-API-KEY-HERE")
    data = api.get_all_countries()

    # You'll see detailed logs including:
    # - Request URLs and parameters
    # - Response status codes
    # - Retry attempts
    # - Error messages

.. note::
   The subscription key is sent in a request header and is never written to the
   logs by ``dtmapi``. The access token in an HNA download link is also kept out
   of ``dtmapi``'s log messages.

   At ``DEBUG`` level, ``urllib3`` (used by ``requests``) logs request URLs including their query
   strings, so the download link's token can appear in its log output. When downloading HNA exports
   with debug logging enabled, raise that logger's level:
   ``logging.getLogger("urllib3").setLevel(logging.INFO)``.

Data Export
-----------

Export Retrieved Data
~~~~~~~~~~~~~~~~~~~~~

By default, data is returned as pandas DataFrames (pass ``to_pandas=False`` to get the raw records instead),
which can be exported with the usual pandas methods:

.. code-block:: python

    from dtmapi import DTMApi

    api = DTMApi(subscription_key="YOUR-API-KEY-HERE")
    data = api.get_idp_admin0_data(CountryName='Sudan', FromRoundNumber=1, ToRoundNumber=10)

    # Export to CSV
    data.to_csv('sudan_idp_data.csv', index=False)

    # Export to Excel (openpyxl is installed with dtmapi)
    data.to_excel('sudan_idp_data.xlsx', index=False)

    # Export to JSON
    data.to_json('sudan_idp_data.json', orient='records', indent=2)

    # Export to Parquet (requires pyarrow or fastparquet)
    data.to_parquet('sudan_idp_data.parquet')

Complete Example
----------------

The following example combines several features:

.. code-block:: python

    import os
    import logging
    from dtmapi import DTMApi, DTMApiError, ValidationError

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize API client with custom settings
    api = DTMApi(
        subscription_key=os.environ["DTMAPI_SUBSCRIPTION_KEY"],
        api_version="v3",
        timeout=60,
        max_retries=5
    )

    try:
        # Get countries
        countries = api.get_all_countries()
        print(f"Available countries: {len(countries)}")

        # Get IDP data for Sudan
        data = api.get_idp_admin0_data(
            CountryName='Sudan',
            FromReportingDate='2020-01-01',
            ToReportingDate='2024-12-31'
        )

        print(f"Retrieved {len(data)} records")

        # Check for gender disaggregation (v3 feature)
        if 'numberMales' in data.columns and 'numberFemales' in data.columns:
            total_males = data['numberMales'].sum()
            total_females = data['numberFemales'].sum()
            print(f"Gender breakdown - Males: {total_males}, Females: {total_females}")

        # Export data
        data.to_csv('sudan_idp_analysis.csv', index=False)
        print("Data exported successfully")

    except ValidationError as e:
        print(f"Validation error: {e}")
    except DTMApiError as e:
        print(f"API error: {e}")

Best Practices
--------------

1. **Use Environment Variables for API Keys**

   Never hardcode API keys in your code:

   .. code-block:: python

      import os
      api = DTMApi(subscription_key=os.environ["DTMAPI_SUBSCRIPTION_KEY"])

2. **Use v3 API for New Projects**

   API v3 includes enhanced demographic data. Only use v2 for legacy compatibility.

3. **Enable Logging During Development**

   Use debug logging to troubleshoot issues:

   .. code-block:: python

      import logging
      logging.basicConfig(level=logging.DEBUG)

4. **Handle Exceptions Appropriately**

   Use specific exception types for better error handling:

   .. code-block:: python

      from dtmapi import ValidationError, DTMAuthenticationError

      try:
          data = api.get_idp_admin0_data(CountryName='Sudan')
      except ValidationError as e:
          # Handle validation errors
          pass
      except DTMAuthenticationError as e:
          # Handle authentication errors
          pass

5. **Fetch All HNA Pages**

   Prefer ``get_all_hna_admin2_data`` over ``get_hna_admin2_data``: the single-page method
   returns only one page of results.

Additional Resources
--------------------

- **DTM Website**: https://dtm.iom.int/
- **API Registration**: https://dtm-apim-portal.iom.int/
- **GitHub Repository**: https://github.com/Displacement-Tracking-Matrix/dtmapi
- **Issue Tracker**: https://github.com/Displacement-Tracking-Matrix/dtmapi/issues

For questions or feedback, contact: dtmdataconsolidation@iom.int
