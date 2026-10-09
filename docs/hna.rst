HNA API Reference
=================

This page contains the API reference for the Humanitarian Needs Assessment
(HNA) endpoints, available from ``dtmapi`` since 0.2.0.

DTMHnaApi Class
---------------

.. autoclass:: dtmapi.DTMHnaApi
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions
----------

.. automodule:: dtmapi.hna.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Shared Client
-------------

Both :class:`dtmapi.DTMApi` and :class:`dtmapi.DTMHnaApi` inherit their request
handling, retry behaviour and authentication from a common base.

.. autoclass:: dtmapi._client.BaseDTMClient
   :members:
   :undoc-members:
