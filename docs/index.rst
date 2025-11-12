.. dtmapi documentation master file, created by
   sphinx-quickstart.

.. image:: https://dtm.iom.int/themes/custom/dtm_global/logo.svg
   :alt: Displacement Tracking Matrix
   :align: center
   :width: 400px
   :target: https://dtm.iom.int

`dtmapi` is a Python package developed by `Displacement Tracking Matrix (DTM) <https://dtm.iom.int/>`_.  
It empowers humanitarian actors, academia, media, governments, and non-governmental organizations to access non-sensitive Internally Displaced Person (IDP) figures, aggregated at multiple administrative levels:

- **Country Level (Admin 0)**
- **First-level Administrative Divisions (Admin 1)**
- **Second-level Administrative Divisions (Admin 2)**

For more background, see the `DTM API overview <https://dtm.iom.int/data-and-analysis/dtm-api>`_.

----

Key Features
------------

- **API Version Support:** Access both v3 (current) and v2 (legacy) API endpoints
- **Enhanced Data Fields (v3):**

  - **Gender Disaggregation:** Male and female population breakdown
  - **Origin of Displacement:** Track geographical origins of displacement
  - **Displacement Reason:** Understand causes (conflict, disasters, etc.)

- **Robust Data Validation:** Automatic validation of parameters (dates, ranges, required fields)
- **Automatic Retry Logic:** Built-in exponential backoff for transient errors
- **Custom Exception Handling:** Clear, specific error messages for different failure scenarios
- **Comprehensive Logging:** Debug and track API interactions
- **Flexible Configuration:** Customizable timeouts and retry settings

----

How to Get a Subscription API Key
---------------------------------

Access to the DTM API now requires a personal API subscription key.

1. Go to the **DTM API Registration Portal**:  
   https://dtm-apim-portal.iom.int/

2. Sign up or log in with personal details such as name, email, job title, and organization.

3. In the **APIs** section, select **API-V3**.

4. Click **Subscribe**.  
   A subscription name may be requested—choose a meaningful name for identification.

5. Once the subscription is activated, the API key can be accessed under the **Profile** section in the top menu bar.

   - The **Primary key** shown there serves as the personal API key.  
   - The available endpoints for this API version are also listed.

6. The API key should be copied and stored securely. It is required for authenticating all requests when using the `dtmapi` Python package.

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

   usage
   dtmapi
