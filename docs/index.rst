.. dtmapi documentation master file, created by
   sphinx-quickstart.

.. image:: https://dtm.iom.int/themes/custom/dtm_global/logo.svg
   :alt: Displacement Tracking Matrix
   :align: center
   :width: 400px
   :target: https://dtm.iom.int

dtmapi Documentation
====================

`dtmapi` is a Python package developed by `Displacement Tracking Matrix (DTM) <https://dtm.iom.int/>`_.  
It empowers humanitarian actors, academia, media, governments, and non-governmental organizations to access non-sensitive Internally Displaced Person (IDP) figures, aggregated at multiple administrative levels:

- **Country Level (Admin 0)**
- **First-level Administrative Divisions (Admin 1)**
- **Second-level Administrative Divisions (Admin 2)**

For more background, see the `DTM API overview <https://dtm.iom.int/data-and-analysis/dtm-api>`_.

----

What's New in Version 3
-----------------------

Version 3 introduces new features for enhanced displacement analysis:

- **Origin of Displacement:**  
  Identify the geographical origin or location where displacement began, offering better tracking of movement patterns.
- **Gender Disaggregation:**  
  Access disaggregated data by gender to support more inclusive and targeted humanitarian responses.
- **Reason for Displacement:**  
  Understand the primary causes of displacement, including conflict, disasters, and other drivers.

----

How to Get a Subscription API Key
---------------------------------

Access to the DTM API now requires a personal API subscription key.

1. **Go to the DTM API Registration Portal:**  
   https://dtm-apim-portal.iom.int/

2. **Sign up or log in** with your personal details (name, email, job title, organization, etc.).

3. **Navigate to the "APIs" section and select "DTM-APIs".**

4. **Click "Subscribe".**  
   You may be asked to enter a subscription name—choose a meaningful name for your subscription.

5. **After your subscription is activated, your API key will be shown.**

   - This is your personal ``Ocp-Apim-Subscription-Key``.
   - The available endpoints for this API version will also be displayed.

6. **Copy and store your API key securely.**  
   You will need this key to authenticate all requests using the ``dtmapi`` Python package.

----

Documentation
-------------

Full documentation is available at: https://dtmapi.readthedocs.io/en/latest/

Source Code
-----------

The source code for ``dtmapi`` is available on `GitHub <https://github.com/Displacement-tracking-Matrix/dtmapi>`_.

----

License
-------

This project is licensed under the MIT License.  
See the `LICENSE <https://github.com/Displacement-Tracking-Matrix/dtmapi/blob/main/LICENSE>`_ file for details.

----

Contact
-------

For any questions or feedback, please contact:  
dtmdataconsolidation@iom.int

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
