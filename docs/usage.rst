Quick Start
===========

This guide provides a quick overview of how to get started with the `dtmapi` library, including installation and usage examples.

Installation
------------

To install `dtmapi`, use `pip`. Run the following command in your terminal:

.. code-block:: bash
    
    pip install dtmapi


Here's a quick example to get you started:

Usage Example
-------------   
.. code-block:: python

   from dtmapi import DTMApi

   # Instantiate the API client with your subscription key.
   api = DTMApi(subscription_key="YOUR-API-KEY-HERE")


Get All Countries
---------------------

.. code-block:: python

    # Get all countries for which DTM data is publicly available through the API.
    all_country_list = api.get_all_countries()
    all_country_list.head()


Get All Operations
---------------------

.. code-block:: python

    # Get all operations for which DTM data is publicly available through the API.
    all_operation_list = api.get_all_operations()
    all_operation_list.head()


Get IDP Admin 0 Data
---------------------

.. code-block:: python

    # Get IDP Admin 0 Data for Ethiopia from Round 1 to Round 10
    idp_admin0_data = api.get_idp_admin0_data(CountryName='Ethiopia', FromRoundNumber=1, ToRoundNumber=10)
    idp_admin0_data.head()

Get IDP Admin 1 Data
---------------------

.. code-block:: python

    # Get IDP Admin 1 Data for Sudan from reporting date 2020-01-01 to 2024-08-15
    idp_admin1_data = api.get_idp_admin1_data(CountryName='Sudan', Admin1Name="Blue Nile", FromReportingDate='2020-01-01', ToReportingDate='2024-08-15')
    idp_admin1_data.head()

Get IDP Admin 2 Data
---------------------

.. code-block:: python

    # Get IDP Admin 2 Data for Lebanon
    idp_admin2_data = api.get_idp_admin2_data(Operation="Displacement due to conflict", CountryName='Lebanon')
    idp_admin2_data.head()





