HNA API Reference
=================

This page contains the API reference for the Humanitarian Needs Assessment
(HNA) endpoints, available from ``dtmapi`` since 0.2.0. For examples, see the
:doc:`usage guide <usage>`. The HNA API requires its own subscription key,
separate from the displacement API key.

DTMHnaApi Class
---------------

.. autoclass:: dtmapi.DTMHnaApi
   :members:
   :exclude-members: AUTH_ERROR, TIMEOUT_ERROR, REQUEST_ERROR, RESPONSE_ERROR, ENV_KEY_NAME, SERVICE_NAME

Exceptions
----------

.. automodule:: dtmapi.hna.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Shared Behavior
---------------

Both :class:`dtmapi.DTMApi` and :class:`dtmapi.DTMHnaApi` inherit their request
handling, retry behavior, and authentication from a common internal base class,
so timeouts, retries, and error handling work the same way in both clients.
