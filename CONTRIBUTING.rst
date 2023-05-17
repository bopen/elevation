
This project is Free and Open Source Software released under the terms of the
`Apache License, Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_.
Contributions are highly welcomed and appreciated. Every little help counts, so do not hesitate!

.. highlight: console


Report a bug
------------

If you encounter any problems, please file a bug report
in the project `issue tracker <https://github.com/bopen/elevation/issues>`_
along with a detailed description.


Submit a pull request
---------------------

Development dependencies are installed by::

    $ pip install -r requirements-tests.txt -r requirements-docs.txt -r requirements-dev.txt

Tests can be run with `pytest <https://pytest.org>`_ and `tox <https://tox.readthedocs.org>`_,
please ensure the coverage at least stays the same before you submit a pull request.


Keeping dependencies uptodate
-----------------------------

Testing in done on version pinned dependencies to ensure reproducibility,
in order to update the pinned version to the latest version run::

    $ pip-compile -U --no-index requirements-tests.in
    $ pip-compile -U --no-index requirements-docs.in
