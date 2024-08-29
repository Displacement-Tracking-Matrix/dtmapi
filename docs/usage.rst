Quick Start
===========

This guide provides a quick overview of how to get started with the `dtmapi` library, including installation and usage examples.

Installation
------------

To install `dtmapi`, use `pip`. Run the following command in your terminal:

.. code-block:: bash
    
    pip install dtmapi


Here's a quick example to get you started:

Get All Country List
---------------------

.. code-block:: python

    import dtmapi

    # Get all countries for which DTM data is publicly available through the API.
    all_country_list = dtmapi.get_all_country_list()
    all_country_list.head()


Get All Operation List
---------------------

.. code-block:: python

    import dtmapi

    # Get all operations for which DTM data is publicly available through the API.
    all_operation_list = dtmapi.get_all_operation_list()
    all_operation_list.head()


Get IDP Admin 0 Data
---------------------

.. code-block:: python

    import dtmapi

    # Get IDP Admin 0 Data for Ethiopia from Round 1 to Round 10
    idp_admin0_data = dtmapi.get_idp_admin0_data(CountryName='Ethiopia', FromRoundNumber=1, ToRoundNumber=10, to_pandas=True)
    idp_admin0_data.head()

Get IDP Admin 1 Data
---------------------

.. code-block:: python

    import dtmapi

    # Get IDP Admin 1 Data for Sudan from reporting date 2020-01-01 to 2024-08-15
    idp_admin1_data = dtmapi.get_idp_admin1_data(CountryName='Sudan', Admin1Name="Blue Nile", FromReportingDate='2020-01-01', ToReportingDate='2024-08-15', to_pandas=True)
    idp_admin1_data.head()

Get IDP Admin 2 Data
---------------------

.. code-block:: python

    import dtmapi

    # Get IDP Admin 2 Data for Lebanon
    idp_admin2_data = dtmapi.get_idp_admin2_data(Operation="Displacement due to conflict", CountryName='Lebanon', to_pandas=True)
    idp_admin2_data.head()





