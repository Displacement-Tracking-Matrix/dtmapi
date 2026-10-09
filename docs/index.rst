.. image:: https://dtm.iom.int/themes/custom/dtm_global/logo.svg
   :alt: Displacement Tracking Matrix
   :align: center
   :width: 400px
   :target: https://dtm.iom.int

.. raw:: html

   <div style="margin-bottom: 2em;"></div>

dtmapi
======

``dtmapi`` is a Python package developed by the `Displacement Tracking Matrix (DTM) <https://dtm.iom.int/>`_.
It enables humanitarian actors, academia, media, governments, and non-governmental organizations to access DTM data from Python:

- **Displacement data** (``DTMApi``): non-sensitive Internally Displaced Person (IDP) figures, aggregated at the
  country (Admin 0), first-level administrative division (Admin 1), and second-level administrative division (Admin 2) levels.
- **Humanitarian Needs Assessment data** (``DTMHnaApi``): needs indicators at the Admin 2 level, with a catalog describing each indicator.

For more background, see the `DTM API overview <https://dtm.iom.int/data-and-analysis/dtm-api>`_.

----

Key Features
------------

- **API Version Support:** Access both v3 (current) and v2 (legacy) displacement endpoints
- **Enhanced Data Fields (v3):**

  - **Gender Disaggregation:** Male and female population breakdown
  - **Origin of Displacement:** Track geographical origins of displacement
  - **Displacement Reason:** Understand causes (conflict, disasters, etc.)

- **Humanitarian Needs Assessment (HNA):** Admin 2 needs indicators, an indicator catalog, automatic pagination, and Excel export
- **pandas Integration:** Results are returned as pandas DataFrames by default
- **Parameter Validation:** Dates, ranges, and required fields are checked before a request is sent
- **Automatic Retries:** Exponential backoff for timeouts, connection errors, and transient HTTP errors
- **Specific Exceptions:** A clear exception hierarchy for authentication, request, response, and timeout failures
- **Logging:** Standard Python logging for tracing API interactions
- **Configurable:** Adjustable timeouts and retry settings

----

How to Get a Subscription API Key
---------------------------------

Access to the DTM API requires a personal API subscription key.

1. Go to the **DTM API Registration Portal**: https://dtm-apim-portal.iom.int/

2. Sign up or log in with personal details such as name, email, job title, and organization.

3. In the **APIs** section, select **API-V3**.

4. Click **Subscribe**.
   A subscription name may be requested; choose a meaningful name for identification.

5. Once the subscription is activated, the API key can be accessed under the **Profile** section in the top menu bar.

   - The **Primary key** shown there serves as the personal API key.
   - The available endpoints for this API version are also listed.

6. Copy the API key and store it securely. It is required to authenticate every request made with ``dtmapi``.
   Never share it or commit it to version control; ``DTMApi`` reads it from the ``DTMAPI_SUBSCRIPTION_KEY``
   environment variable when no key is passed.

HNA Subscription Key
~~~~~~~~~~~~~~~~~~~~

The HNA API is a separate subscription with its own key; the displacement key does not work for it.
To get one, follow the same steps in the portal, but subscribe to the **HNA** API instead of **API-V3**.
``DTMHnaApi`` reads it from the ``DTMHNA_SUBSCRIPTION_KEY`` environment variable when no key is passed.

----

Source Code
-----------

The source code for ``dtmapi`` is available on `GitHub <https://github.com/Displacement-Tracking-Matrix/dtmapi>`_.

----

License
-------

This project is licensed under the MIT License.
See the `LICENSE <https://github.com/Displacement-Tracking-Matrix/dtmapi/blob/main/LICENSE>`_ file for details.

----

Contact
-------

For questions or feedback, please contact dtmdataconsolidation@iom.int.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage
   dtmapi
   hna
