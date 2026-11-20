:html_theme.sidebar_secondary.remove:
:notoc:

Welcome to PM4Py's Documentation!
===================================

``PM4Py`` is a Python library implementing a variety of `process mining <https://en.wikipedia.org/wiki/Process_mining>`_ algorithms.

.. code-block:: python

   import pm4py

   if __name__ == "__main__":
       log = pm4py.read_xes('<path-to-xes-log-file.xes>')
       process_model = pm4py.discover_bpmn_inductive(log)
       pm4py.view_bpmn(process_model)

In this documentation, you can find all relevant information to set up ``PM4Py`` and start your process mining journey.
Please consult the contents listed below to navigate the documentation.

Happy #ProcessMining!

.. grid:: 1 1 2 2
    :gutter: 3
    :margin: 4 4 0 0

    .. grid-item-card::
        :text-align: center
        :shadow: md

        .. raw:: html

            <div style="font-size: 4em; padding: 20px 0;">
                <i class="fa-solid fa-rocket" style="color: #333333;"></i>
            </div>

        **Getting Started**
        ^^^

        New to PM4Py? Read through our installation guide or get an introduction to process mining using PM4Py.

        +++
        .. button-ref:: getting_started_index
            :expand:
            :color: light
            :click-parent:

            To the getting started guides

    .. grid-item-card::
        :text-align: center
        :shadow: md

        .. raw:: html

            <div style="font-size: 4em; padding: 20px 0;">
                <i class="fa-solid fa-code" style="color: #333333;"></i>
            </div>

        **API Reference**
        ^^^

        Explore the PM4Py API by going through all available methods.

        +++
        .. button-ref:: api
            :expand:
            :color: light
            :click-parent:

            To the API reference

    .. grid-item-card::
        :text-align: center
        :shadow: md

        .. raw:: html

            <div style="font-size: 4em; padding: 20px 0;">
                <i class="fa-solid fa-bullhorn" style="color: #333333;"></i>
            </div>

        **Release Notes**
        ^^^

        Want to know what's new? Check out the release notes for the latest updates and bug fixes.

        +++
        .. button-ref:: release_notes
            :expand:
            :color: light
            :click-parent:

            To the release notes

    .. grid-item-card::
        :text-align: center
        :shadow: md

        .. raw:: html

            <div style="font-size: 4em; padding: 20px 0;">
                <i class="fa-brands fa-github" style="color: #333333;"></i>
            </div>

        **GitHub Repository**
        ^^^

        Want to contribute? Visit our Github Page!

        +++
        .. button-link:: https://github.com/process-intelligence-solutions/pm4py
            :expand:
            :color: light
            :click-parent:

            To our Github Repository

.. toctree::
   :hidden:
   :maxdepth: 2

   getting_started_index
   concept_drift
   api
   release_notes
