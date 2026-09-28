
This project is Free and Open Source Software released under the terms of the
`Apache License, Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_.
Contributions are highly welcomed and appreciated. Every little bit of help counts, so do not hesitate!

.. highlight: console


Report a bug
------------

If you encounter any problems, please file a bug report
in the project `issue tracker <https://github.com/bopen/elevation/issues>`_
along with a detailed description.


Submit a pull request
---------------------

Development dependencies are installed and the environment kept up to date by
`uv <https://docs.astral.sh/uv/>`_::

    $ uv sync

The ``Makefile`` wraps the common development tasks::

    $ make              # qa + unit-tests + check-typing
    $ make qa           # run all pre-commit hooks
    $ make unit-tests   # run the tests with coverage

Please ensure the coverage at least stays the same before you submit a pull request.


Keeping dependencies up to date
-------------------------------

The ``uv.lock`` file pins all dependencies to ensure reproducibility,
to upgrade them to the latest allowed versions run::

    $ uv lock --upgrade
    $ uv sync
