Getting Started
===============

Understanding Process Mining
----------------------------

.. raw:: html

    <!--<iframe width="560" height="315" src="https://www.youtube.com/embed/XLHtvt36g6U" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>-->
    <a href="https://www.youtube.com/embed/XLHtvt36g6U" target="_blank" rel="noopener noreferrer">→ Watch on YouTube: pm4py tutorials - tutorial #1 What is Process Mining?</a>


In this section, we explain what process mining is all about. 
Note that this page describes the basics of process mining, i.e., it is not a full-fledged reference of every possible aspect of process mining. 
Therefore, for a more detailed overview of process mining, we recommend looking at the `Coursera MOOC on Process Mining <https://www.coursera.org/learn/process-mining>`_ and the `seminal book of Wil van der Aalst <https://www.springer.com/gp/book/9783662498507>`_. 
Furthermore, before you begin, please install PM4Py on your system, i.e., as described in the :doc:`install` section.

Processes in our Modern World
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The vast majority of companies active in virtually any domain execute a process. 
Whether the core business of a company is to deliver a product, e.g., manufacture a car, cook a delicious pizza, etc., or provide a service, e.g., providing you with a mortgage to buy your dream house, paying back your insurance claim, etc., for efficient delivery of your product/service, processes are executed. 
Hence, a natural question is: “What is a process?”. 
In general, several notions of the concept of a process exist. 
However, in process mining, we typically assume the following conceptual definition:

"A **process** represents a **collection of activities** that we **execute** to achieve a **certain goal**."

For example, consider the burger restaurant just around the corner, which also delivers burgers.
When you call the restaurant to order your beloved burger, the first action taken by the employee, let’s call her **Lucy**, taking your call, is to *take your order*. 
Let’s assume you go for a tasty cheeseburger with a can of soda. 
After Lucy has *entered your order in the cash register*, she *asks for your address*, which she adds to the order. 
Finally, she *asks for your preferred means of payment*, after which she provides you with a rough estimate of the time until delivery. 
When Lucy finishes the call, she *prints your order* and hands it over to the chef, let’s call him **Luigi**. 
Since you’ve called relatively early, Luigi can start *preparing your burger* right away. 
At the same time, Lucy *takes a can of soda out of the refrigerator* and places it on the counter. 
A new call comes in from a different customer, which she handles roughly the same way as yours. 
When Luigi *finishes your burger*, he *slides it into a carton box* and hands the box over to Lucy. 
Lucy *wraps the order* in a bag. 
She then hands the bag with your burger and soda to **Mike**, which uses a fancy electrical bicycle to *bring your order to your home*.

In this small example, let’s assume that we are interested in the process, i.e., the collection of activities performed for your order. 
Based on the scenario we just presented, the steps look as follows:


1. **Lucy** *takes your order*
#. **Lucy** *notes down your address*
#. **Lucy** *notes down your preferred payment method*
#. **Luigi** *prepares your burger*
#. **Lucy** *grabs your can of soda*
#. **Luigi** *puts your burger in a box*
#. **Lucy** *wraps your order*
#. **Mike** *delivers your order*

Importing Your First Event Log
------------------------------
In this section, we explain how to import (and export) event data in PM4Py. We assume that you are familiar with the conceptual basics of process mining, i.e., as described in the previous section.

File Types: CSV and XES
~~~~~~~~~~~~~~~~~~~~~~~~
As explained in the previous section, process mining exploits Event Logs to generate knowledge of a process. A wide variety of information systems, e.g., SAP, ORACLE, SalesForce, etc., allow us to extract, in one way or the other, event logs similar to the example event log presented in Table 1 and Table 2. All the examples we show in this section and all algorithms implemented in pm4py assume that we have already extracted the event data into an appropriate event log format. Hence, the core of pm4py does not support any data extraction features. However, we provide solutions for data extraction purposes, i.e., please inspect the corresponding `solutions page </solution-connectors>`_.

In order to support interoperability between different process mining tools and libraries, two standard data formats are used to capture event logs, i.e., Comma Separated Value (CSV) files and eXtensible Event Stream (XES) files. CSV files resemble the example tables shown in the previous section, i.e., Table 1 and Table 2. Each line in such a file describes an event that occurred. The columns represent the same type of data, as shown in the examples, e.g., the case for which the event occurred, the activity, the timestamp, the resource executing the activity, etc. The XES file format is an XML-based format that allows us to describe process behavior. We will not go into details w.r.t. the format of XES files, i.e., we refer to `https://www.xes-standard.org <https://www.xes-standard.org>`_ for an overview.

In the remainder of this tutorial, we will use an oftenly used dummy example event log to explain the basic process mining operations. The process that we are considering is a simplified process related to customer complaint handling, i.e., *taken from the book of van der Aalst*. The process, and the event data we are going to use, looks as follows.

.. image:: https://pm4py.fit.fraunhofer.de/static/assets/images/getting_started/bpmn_running_example.png

*Figure 3: Running example BPMN-based process model describing the behavior of the simple process that we use in this tutorial.*

Let’s get started! We have prepared a small sample event log, containing behavior similar equal to the process model in Figure 3. `You can find the sample event log here </static/assets/data/getting_started/running-example.csv>`_. Please download the file and store it somewhere on your computer, e.g., your Downloads folder (On Windows: this is 'C:/Users/user_name/Dowloads'). Consider Figure 4, in which we depict the first 25 rows of the example file.

.. image:: https://pm4py.fit.fraunhofer.de/static/assets/images/getting_started/csv_snapshot.png

*Figure 4: Running example csv data set which we will use in this tutorial.*

Note that, the data depicted in Figure 4 describes a table, however, in text format. Each line in the file corresponds to a row in the table. Whenever we encounter a ‘;’ symbol on a line, this implies that we are ‘entering’ the next column. The first line (i.e., row) specifies the name of each column. Observe that, in the data table described by the file, we have 5 columns, being: *case_id*, *activity*, *timestamp*, *costs* and *resource*. Observe that, similar to our previous example, the first column represents the case identifier, i.e., allowing us to identify what activity has been logged in the context of what instance of the process. The second column shows the activity that has been performed. The third column shows at what point in time the activity was recorded. In this example data, additional information is present as well. In this case, the fourth column tracks the costs of the activity, whereas the fifth row tracks what resource has performed the activity.

Before we go into loading the example file into PM4Py, let us briefly take a look at the data. Observe that, lines 2-10 show the events that have been recorded for the process identified by case identifier 3. We observe that first a register request activity was performed, followed by the examine casually, check ticket, decide,reinitiate request, examine thoroughlycheck ticket,decide, and finally, pay compensation activities. Note that, indeed, in this case the recorded process instance behaves as described by the model depicted in Figure 3.

Loading CSV Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

	<!--<iframe width="560" height="315" src="https://www.youtube.com/embed/bWOKVx0PO6g" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>-->
    <a href="https://www.youtube.com/embed/bWOKVx0PO6g" target="_blank" rel="noopener noreferrer">→ Watch on YouTube: pm4py tutorials - tutorial #2 Importing CSV Files</a>


Given that we have familiarized ourselves with event logs and a way to represent event logs in a CSV file, it is time to start doing some process mining! We are going to load the event data, and, we are going to count how many cases are present in the event log, as well as the number of events. Note that, for all this, we are effectively using a third-party library called `pandas <https://pandas.pydata.org>`_. We do so because pandas is the de-facto standard of loading/manipulating csv-based data. Hence, *any process mining algorithm implemented in PM4Py, using an event log as an input, can work directly with a pandas file!*

.. code-block:: python3

    import pandas


    def import_csv(file_path):
        event_log = pandas.read_csv(file_path, sep=';')
        num_events = len(event_log)
        num_cases = len(event_log.case_id.unique())
        print("Number of events: {}\nNumber of cases: {}".format(num_events, num_cases))


    if __name__ == "__main__":
        import_csv("C:/Users/demo/Downloads/running-example.csv")

*Example 1: Loading an event log stored in a CSV file and computing the number of cases and the number of events in the file. In this example, no PM4Py is used yet, it is all being handled using pandas. If you run the code yourself, make sure to replace the path 'C:/Users/demo/Downloads/running-example.csv', to the appropriate path on your computer containing the running example file.*

We will quickly go through the above example code. In the first line, we import the pandas library. The last lines (containing the if-statement) make sure that the code, when pasted, runs on its own (we will omit these lines from future examples). The core of the script is the function **import_csv**. As an input parameter, it requires the path to the csv file. The script uses the pandas read_csv-function, to load the event data. To calculate the number of events, we simply query the length of the data frame, i.e., by calling **len(event_log)**. To calculate the number of cases, we use a built-in pandas function to return the number of unique values of the case_id column, i.e., **event_log.case_id.unique()**. Since that function returns a pandas built-in array object containing all the values of the column, we again query for its length. Note that, as is often the case when programming, there is a wide variety of ways to compute the aforementioned example statistics on the basis of a given CSV file.

Now we have loaded our first event log, it is time to put some PM4Py into the mix. Let us assume that we are not only interested in the number of events and cases, yet, we also want to figure out what activities occur first, and what activities occur last in the traces described by the event log. PM4Py has a specific built-in function for this, i.e., **get_start_activities()** and **get_end_activities()** respectively. Consider Example 2, in which we present the corresponding script.

.. code-block:: python3

    import pandas
    import pm4py


    def import_csv(file_path):
        event_log = pandas.read_csv(file_path, sep=';')
        event_log = pm4py.format_dataframe(event_log, case_id='case_id', activity_key='activity', timestamp_key='timestamp')
        start_activities = pm4py.get_start_activities(event_log)
        end_activities = pm4py.get_end_activities(event_log)
        print("Start activities: {}\nEnd activities: {}".format(start_activities, end_activities))

    if __name__ == "__main__":
        import_csv("csv_file.csv")

*Example 2: Loading an event log stored in a CSV file and computing the start and end activities of the traces in the event log. If you run the code yourself, make sure to point the file path to the appropriate path on your computer containing the running example file.*

Note that, we now import pandas and pm4py. The first line of our script again loads the event log stored in CSV format as a data frame. The second line transforms the event data table into a format that can be used by any process mining algorithm in pm4py. That is, the **format_dataframe()**-function creates a copy of the input event log, and renames the assigned columns to standardized column names used in pm4py. In our example, the column case_id is renamed to case:concept:name, the activity column is renamed to concept:name and the timestamp column is renamed to time:timestamp. The underlying reasons for using the aforementioned standard names is primarily related to XES-based (the other file format that we will look at shortly) legacy. Hence, it is advisable to always import a csv based log as follows.

Note that, in this example, the value of the arguments, i.e., *sep*, *case_id*, *activity_key* and *timestamp_key* are depending on the input data. To obtain the activities that occur first and, respectively, last in any trace in the event log, we call the pm4py.get_start_activities(event_log) and the pm4py.get_end_activities(event_log) functions. The functions return a dictionary, containing the activities as a key, and, the number of observations (i.e., number of traces in which they occur first, respectively, last) in the event log.

PM4Py exploits a built-in pandas function to detect the format of the timestamps in the input data automatically. However, pandas looks at the timestamp values in each row in isolation. In some cases, this can lead to problems. For example, if the provided value is 2020-01-18, i.e., first the year, then the month, and then the day of the date, in some cases, a value of 2020-02-01 may be interpreted wrongly as January 2nd, i.e., rather than February 1st. To alleviate this problem, an additional parameter can be provided to the **format_dataframe()** method, i.e., the timest_format parameter. In this example, the timestamp format is %Y-%m-%d %H:%M:%S%z. In general, we advise to specify the timestamp format!

Loading XES Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

	<!--<iframe width="560" height="315" src="https://www.youtube.com/embed/pmpN3A_h2sQ" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>-->
    <a href="https://www.youtube.com/embed/pmpN3A_h2sQ" target="_blank" rel="noopener noreferrer">→ Watch on YouTube: pm4py tutorials - tutorial #3 Importing XES Files</a>

Next to CSV files, event data can also be stored in an XML-based format, i.e., in XES files. In an XES file, we can describe a containment relation, i.e., a log contains a number of traces, which in turn contain several events. Furthermore, an object, i.e., a log, trace, or event, is allowed to have attributes. The advantage is that certain data attributes that are constant for a log or a trace, can be stored at that level. For example, assume that we only know the total costs of a case, rather than the costs of the individual events. If we want to store this information in a CSV file, we either need to replicate this information (i.e., we can only store data in rows, which directly refer to events), or, we need to explicitly define that certain columns only get a value once, i.e., referring to case-level attributes. The XES standard more naturally supports the storage of this type of information.

Consider Figure 5, in which we depict a snapshot of the running example data stored in the .xes file format. The complete file can be downloaded
`here <https://pm4py.fit.fraunhofer.de/static/assets/data/getting_started/running-example.xes>`_.

.. image:: https://pm4py.fit.fraunhofer.de/static/assets/images/getting_started/csv_snapshot.png

*Figure 5: Running example xes data set.*

Observe that the trace with number 1 (reflected by the [string key=”concept:name”]-tag on line 9) is the first trace recorded in this event log. The first event of the trace represents the “register request” activity executed by Pete. The second event is the “examine thoroughly” activity, executed by Sue, etc. We will not elaborate on the XES standard in detail here, i.e., we refer to the `XES homepage <http://www.xes-standard.org/>`_, and, to our `video tutorial <https://www.youtube.com/watch?v=pmpN3A_h2sQ&t=1785s&ab_channel=ProcessMiningforPython>`_ on importing XES for more information.

Importing an XES file is fairly straightforward. PM4Py has a special **read_xes()**-function that can parse a given xes file and load it in PM4Py, i.e., as an Event Log object. Consider the following code snippet, in which we show how to import an XES event log. Like the previous example, the script outputs activities that can start and end a trace.

.. code-block:: python3

    def import_xes(file_path):
        event_log = pm4py.read_xes(file_path)
        start_activities = pm4py.get_start_activities(event_log)
        end_activities = pm4py.get_end_activities(event_log)
        print("Start activities: {}\nEnd activities: {}".format(start_activities, end_activities))

    if __name__ == "__main__":
        import_xes("C:/Users/demo/Downloads/running-example.xes")

Exporting Event Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

	<!--<iframe width="560" height="315" src="https://www.youtube.com/embed/gVnfG6xLIxI" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>-->
    <a href="https://www.youtube.com/embed/gVnfG6xLIxI" target="_blank" rel="noopener noreferrer">→ Watch on YouTube: pm4py tutorials - tutorial #6 exporting event data</a>


Now we are able to import event data into PM4Py, let’s take a look at the opposite, i.e., exporting event data. Exporting of event logs can be very useful, e.g., we might want to convert a .csv file into a .xes file or we might want to filter out certain (noisy) cases and save the filtered event log. Like importing, exporting of event data is possible in two ways, i.e., exporting to csv (using pandas) and exporting to xes. In the upcoming sections, we show how to export an event log stored as a pandas data frame into a csv file, a pandas data frame as a xes file, a PM4Py event log object as a csv file and finally, a PM4Py event log object as a xes file.

Storing a Pandas Data Frame as a csv file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Storing an event log that is represented as a pandas dataframe is straightforward, i.e., we can directly use the **to_csv** function of the pandas DataFrame object. Consider the following example snippet of code, in which we show this functionality.

Note that the example code imports the running example csv file as a pandas data frame, and, exports it to a csv file at the location ‘C:/Users/demo/Desktop/running-example-exported.csv’. Note that, by default, pandas uses a ‘,’-symbol rather than ‘;’-symbol as a column separator.

.. code-block:: python3

    import pandas as pd

    if __name__ == "__main__":
        event_log = pm4py.format_dataframe(pd.read_csv('C:/Users/demo/Downloads/running-example.csv', sep=';'), case_id='case_id',
        activity_key='activity', timestamp_key='timestamp')
        event_log.to_csv('C:/Users/demo/Desktop/running-example-exported.csv')

Storing a Pandas Data Frame as a .xes file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is also possible to store a pandas data frame to a xes file. This is simply done by calling the **pm4py.write_xes()** function. You can pass the dataframe as an input parameter to the function, i.e., pm4py handles the internal conversion of the dataframe to an event log object prior to writing it to disk. Note that this construct only works if you have formatted the data frame, i.e., as highlighted earlier in the importing CSV section.

.. code-block:: python3

    import pandas
    import pm4py

    if __name__ == "__main__":
        event_log = pm4py.format_dataframe(pandas.read_csv('C:/Users/demo/Downloads/running-example.csv', sep=';'), case_id='case_id',
                                               activity_key='activity', timestamp_key='timestamp')
        pm4py.write_xes(event_log, 'C:/Users/demo/Desktop/running-example-exported.xes')

Storing an Event Log object as a .csv file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In some cases, we might want to store an event log object, e.g., obtained by importing a .xes file, as a csv file. For example, certain (commercial) process mining tools only support csv importing. For this purpose, pm4py offers conversion functionality that allows you to convert your event log object into a data frame, which you can subsequently export using pandas.

.. code-block:: python3

    import pm4py

    if __name__ == "__main__":
        event_log = pm4py.read_xes('C:/Users/demo/Downloads/running-example.xes')
        df = pm4py.convert_to_dataframe(event_log)
        df.to_csv('C:/Users/demo/Desktop/running-example-exported.csv')

Storing an Event Log object as a .xes file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Storing an event log object as a .xes file is rather straightforward. In pm4py, the **write_xes()** method allows us to do so. Consider the simple example script below in which we show an example of this functionality.

.. code-block:: python3

    import pm4py

    if __name__ == "__main__":
        event_log = pm4py.read_xes(C:/Users/demo/Downloads/running-example.xes)
        pm4py.write_xes(event_log, 'C:/Users/demo/Desktop/running-example-exported.xes')

Pre-Built Event Log Filters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. raw:: html

	<!--<iframe width="560" height="315" src="https://www.youtube.com/embed/alkZkhK2mAo" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>-->
    <a href="https://www.youtube.com/embed/alkZkhK2mAo" target="_blank" rel="noopener noreferrer">→ Watch on YouTube: pm4py tutorials - tutorial #5: Playing with Event Data; Shipped Filters</a>

There are various pre-built filters in PM4Py, which make commonly needed process mining filtering functionality a lot easier. In the upcoming list, we briefly give an overview of these functions. We describe how to call them, their main input parameters and their return objects.

* **filter_start_activities(log, activities, retain=True)**; This function filters the given event log object (either a data frame or a PM4Py event log object) based on a given set of input activity names that need to occur at the starting point of a trace. If we set retain to False, we remove all traces that contain any of the specified activities as their first event.
* **filter_end_activities(log, activities, retain=True)**; Similar functionality to the start activity filter. However, in this case, the filter is applied for the activities that occur at the end of a trace.
* **filter_event_attribute_values(log, attribute_key, values, level="case", retain=True)**; Filters an event log (either data frame or PM4Py EventLog object) on event attributes. The attribute_key is a string representing the attribute key to filter, the values parameter allows you to specify a set of allowed values. If the level parameter is set to 'case', then any trace that contains at least one event that matches the attribute-value combination is retained. If the level parameter value is set to 'event', only the events are retained that describe the specified value. Setting retain to False inverts the filter.
* **filter_trace_attribute_values(log, attribute_key, values, retain=True)**; Keeps (or removes if retain is set to False) only the traces that have an attribute value for the provided attribute_key and listed in the collection of corresponding values.
* **filter_variants(log, variants, retain=True)**; Keeps those traces that correspond to a specific activity execution sequence, i.e., known as a variant. For example, in a large log, we want to retain all traces that describe the execution sequence 'a', 'b', 'c'. The variants parameter is a collection of lists of activity names.
* **filter_directly_follows_relation(log, relations, retain=True)**; This function filters all traces that contain a specified 'directly follows relation'. Such a relation is simply a pair of activities, e.g., ('a','b') s.t., 'a' is directly followed by 'b' in a trace. For example, the trace <'a','b','c','d'> contains directly follows pairs ('a','b'), ('b','c') and ('c','d'). The relations parameter is a set of tuples, containing activity names. The retain parameter allows us to express whether or not we want to keep or remove the mathcing traces.
* **filter_eventually_follows_relation(log, relations, retain=True)** This function allows us to match traces on a generalization of the directly follows relation, i.e., an arbitrary number of activities is allowed to occur in-between the input relations. For example, when we call the function with a relation ('a','b'), any trace in which we observe activity 'a' at some point, to be followed later by activity 'b', again at some point, adheres to this filter. For example, a trace <'a','b','c','d'> contains eventually follows pairs ('a','b'), ('a','c') ('a','d'), ('b','c'), ('b','d') and ('c','d'). Again, the relations parameter is a set of tuples, containing activity names and the retain parameter allows us to express whether or not we want to keep or remove the matching traces.
* **filter_time_range(log, dt1, dt2, mode='events')**; Filters the event log based on a given time range, defined by timestamps dt1 and dt2. The timestamps should be of the form datetime.datetime. The filter has three modes (default: 'events'):

    * *'events'*; Retains all events that fall in the provided time range. Removes any empty trace in the filtered event log.
    * *'traces_contained'*; Retains any trace that is completely 'contained' within the given time frame. For example, this filter is useful if one is interested to retain all full traces in a specific day/month/year.
    * *'traces_intersecting'*; Retains any trace that has at least one event that falls into the given time range.

Consider the example code below, in which we provide various example applications of the mentioned filtering functions, using the running example event log. Try to copy-paste each line in your own environment and play around with the resulting filtered event log to get a good idea of the functionality of each filter. Note that, all functions shown below also work when providing a dataframe as an input!

.. code-block:: python3

    import pm4py
    import datetime as dt

    if __name__ == "__main__":
        log = pm4py.read_xes('C:/Users/demo/Downloads/running-example.xes')

        filtered = pm4py.filter_start_activities(log, {'register request'})

        filtered = pm4py.filter_start_activities(log, {'register request TYPO!'})

        filtered = pm4py.filter_end_activities(log, {'pay compensation'})

        filtered = pm4py.filter_event_attribute_values(log, 'org:resource', {'Pete', 'Mike'})

        filtered = pm4py.filter_event_attribute_values(log, 'org:resource', {'Pete', 'Mike'}, level='event')

        filtered = pm4py.filter_trace_attribute_values(log, 'concept:name', {'3', '4'})

        filtered = pm4py.filter_trace_attribute_values(log, 'concept:name', {'3', '4'}, retain=False)

        filtered = pm4py.filter_variants(log, [
            ['register request', 'check ticket', 'examine casually', 'decide', 'pay compensation']])

        filtered = pm4py.filter_variants(log, [
            ['register request', 'check ticket', 'examine casually', 'decide', 'reject request']])

        filtered = pm4py.filter_directly_follows_relation(log, [('check ticket', 'examine casually')])

        filtered = pm4py.filter_eventually_follows_relation(log, [('examine casually', 'reject request')])

        filtered = pm4py.filter_time_range(log, dt.datetime(2010, 12, 30), dt.datetime(2010, 12, 31), mode='events')

        filtered = pm4py.filter_time_range(log, dt.datetime(2010, 12, 30), dt.datetime(2010, 12, 31),
                                           mode='traces_contained')

        filtered = pm4py.filter_time_range(log, dt.datetime(2010, 12, 30), dt.datetime(2010, 12, 31),
                                           mode='traces_intersecting')


Discovering Your First Process Model
------------------------------------

Since we have studied basic conceptual knowledge of process mining and event data munging and crunching, we focus on process discovery. As indicated, the goal is to discover, i.e., primarily completely automated and algorithmically, a process model that accurately describes the process, i.e., as observed in the event data. For example, given the running example event data, we aim to discover the process model that we have used to explain the running example's process behavior, i.e., Figure 3. This section briefly explains what modeling formalisms exist in PM4Py while applying different process discovery algorithms. Secondly, we give an overview of the implemented process discovery algorithms, their output type(s), and how we can invoke them. Finally, we discuss the challenges of applying process discovery in practice.

.. raw:: html

	<!--<iframe width="560" height="315" src="https://www.youtube.com/embed/BJMp763Ye_o" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>-->
    <a href="https://www.youtube.com/embed/BJMp763Ye_o" target="_blank" rel="noopener noreferrer">→ Watch on YouTube: pm4py tutorials - tutorial #7 process discovery</a>

Obtaining a Process Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are three different process modeling notations that are currently supported in PM4Py. These notations are: BPMN, i.e., models such as the ones shown earlier in this tutorial, Process Trees and Petri nets. A Petri net is a more mathematical modeling representation compared to BPMN. Often the behavior of a Petri net is more difficult to comprehend compared to BPMN models. However, due to their mathematical nature, Petri nets are typically less ambiguous (i.e., confusion about their described behavior is not possible). Process Trees represent a strict subset of Petri nets and describe process behavior in a hierarchical manner. In this tutorial, we will focus primarily on BPMN models and process trees. For more information about Petri nets and their application to (business) process modeling (from a ‘workflow’ perspective), we refer to
`this article <https://www.researchgate.net/profile/Wil_Aalst/publication/220337578_The_Application_of_Petri_Nets_to_Workflow_Management/links/0deec517a563a45197000000/The-Application-of-Petri-Nets-to-Workflow-Management.pdf?_sg%5B0%5D=2TrqDbNsoZEr67XgOwI_9qxtlO_S1HJFHn8edW7aE0fMWzmsY0D1GhrsbRXdtZhTLvQ1KcSm9pkLzooDMl-eRg.DhnNamQg4EvK8MAwucwkB1VDke7eNq0E4jxMAa2IMXXZtvr9k1PPiwZpQEt1Z2iqkdkN-SOlWyjFloP-BivLow&_sg%5B1%5D=XeHToX2_7feAtM6yO395-HEYttSzdWJeiLaGlD_7Dn3hRXYnVXya0-dHm5RWmjX22gF3ton7d7FSzF6FjL_NYZCQzRvJuPg4zPWnk_HCe0xj.DhnNamQg4EvK8MAwucwkB1VDke7eNq0E4jxMAa2IMXXZtvr9k1PPiwZpQEt1Z2iqkdkN-SOlWyjFloP-BivLow&_iepl=>`_.

Interestingly, none of the algorithms implemented in PM4Py directly discovers a BPMN model. However, any process tree can easily be translated to a BPMN model. Since we have already discussed the basic operators of BPMN models, we will start with the discovery of a process tree, which we convert to a BPMN model. Later, we will study the ‘underlying’ process tree. The algorithm that we are going to use is the ‘Inductive Miner’; More details about the (inner workings of the) algorithm can be found in
`this presentation <http://www.processmining.org/_media/presentations/2013/petri_nets.pptx>`_ and in `this article <http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.396.197&rep=rep1&type=pdf>`_. Consider the following code snippet. We discover a BPMN model (using a conversion from process tree to BPMN) using the inductive miner, based on the running example event data set.

.. code-block:: python3

    import pm4py

    if __name__ == "__main__":
        log = pm4py.read_xes('C:/Users/demo/Downloads/running-example.xes')

        process_tree = pm4py.discover_process_tree_inductive(log)
        bpmn_model = pm4py.convert_to_bpmn(process_tree)
        pm4py.view_bpmn(bpmn_model)


Note that the resulting process model is the following image:

.. image:: https://pm4py.fit.fraunhofer.de/static/assets/images/getting_started/bpmn_inductive_running_example.png

*Figure 6: BPMN model discovered based on the running example event data set, using the Inductive Miner implementation of PM4Py.*

Observe that the process model that we discovered, is indeed the same model as the model that we have used before, i.e., as shown in Figure 3.

As indicated, the algorithm used in this example actually discovers a Process Tree. Such a process tree is, mathematically speaking, a
`rooted tree <https://en.wikipedia.org/wiki/Tree_(graph_theory)>`_ annotated with ‘control-flow’ information. We’ll first use the following code snippet to discover a process tree based on the running example, and, afterwards shortly analyze the model.

.. code-block:: python3

    import pm4py

    if __name__ == "__main__":
        log = pm4py.read_xes('C:/Users/demo/Downloads/running-example.xes')

        process_tree = pm4py.discover_process_tree_inductive(log)
        pm4py.view_process_tree(process_tree)


.. image:: https://pm4py.fit.fraunhofer.de/static/assets/images/getting_started/process_tree_running_example.png

*Figure 7: Process Tree model discovered based on the running example event data set, using the Inductive Miner implementation of PM4Py.*

We the process tree model from top to bottom. The first circle, i.e., the ‘root’ of the process tree, describes a ‘->’ symbol. This means that, when srolling further down, the process described by the model executes the ‘children’ of the root from left to right. Hence, first “register request” is executed, followed by the circle node with the ‘*’ symbol, finally to be followed by the node with the ‘X’ symbol. The node with the ‘*’ represents ‘repeated behavior’, i.e., the possibility to repeat the behavior. When scrolling further down, the left-most ‘subtree’ of the ‘*’-operator is always executed, the right-most child (in this case, “reinitiate request”) triggers a repeated execution of the left-most child. Observe that this is in line with the process models we have seen before, i.e., the “reinitiate request” activity allows us to repeat the behavior regarding examinations and checking the ticket. When we go further down below in the subtree of the ‘*’-operator, we again observe a ‘->’ node. Hence, its left-most child is executed first, followed by its right-most child (“decide”). The left-most child of the ‘->’ node has a ‘+’ symbol. This represents concurrent behavior; hence, its children can be executed simultaneously or in any order. Its left-most child is the “check ticket” activity. Its right-most child is a node with an ‘X’ symbol (just like the right-most child of the tree's root). This represents an exclusive choice, i.e., one of the children is executed (either “examine casually” or “examine thoroughly”). Observe that the process tree describes the exact same behavior as the BPMN models shown before.

Obtaining a Process Map
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many `commercial process mining solutions <https://www.gartner.com/reviews/market/process-mining>`_ do not provide extended support for discovering process models. Often, as a main visualization of processes, process maps are used. A process map contains activities and connections (by means of arcs) between them. A connection between two activities usually means that there some form of precedence relation. In its simplest form, it means that the ‘source’ activity directly precedes the ‘target’ activity. Let’s quickly take a look at a concrete example! Consider the following code snippet, in which we learn a ‘Directly Follows Graph’ (DFG)-based process map:

.. code-block:: python3

    import pm4py

    if __name__ == "__main__":
        log = pm4py.read_xes('C:/Users/demo/Downloads/running-example.xes')

        dfg, start_activities, end_activities = pm4py.discover_dfg(log)
        pm4py.view_dfg(dfg, start_activities, end_activities)



.. image:: https://pm4py.fit.fraunhofer.de/static/assets/images/getting_started/dfg_running_example.png

*Figure 8: Process Map (DFG-based) discovered based on the running example event data set.*

The **pm4py.discover_dfg(log)** function returns a triple. The first result, i.e., called dfg in this example, is a dictionary mapping pairs of activities that follow each other directly, to the number of corresponding observations. The second and third arguments are the start and end activities observed in the event log (again counters). In the visualization, the green circle represents the start of any observed process instance. The orange circle represents the end of an observed process instance. In 6 cases, the register request is the first activity observed (represented by the arc labeled with value 6). In the event log, the check ticket activity is executed directly after the register request activity. The examine thoroughly activity is following registration once, examine casually follows 3 times. Note that, indeed, in total, the register activity is followed by 6 different events, i.e., there are 6 traces in the running example event log. However, note that there are typically much more relations observable compared to the number of cases in an event log. Even using this simple event data, the DFG-based process map of the process is much more complex than the process models learned earlier. Furthermore, it is much more difficult to infer the actual execution of the process based on the process map. Hence, when using process maps, one should be very carefully when trying to comprehend the actual process.

In PM4Py, we also implemented the `Heuristics Miner <https://ieeexplore.ieee.org/iel5/5937059/5949295/05949453.pdf>`_, a more advanced process map discovery algorithm, compared to its DFG-based alternative. We won’t go into the algorithmic details here, however, in a HM-based process map, the arcs between activities represent observed concurrency. For example, the algorithm is able to detect that the ticket check and examination are concurrent. Hence, these activities will not be connected in the process map. As such, a HM-based process map is typically simpler compared to a DFG-based process map.

.. code-block:: python3

    import pm4py

    if __name__ == "__main__":
        log = pm4py.read_xes('C:/Users/demo/Downloads/running-example.xes')

        map = pm4py.discover_heuristics_net(log)
        pm4py.view_heuristics_net(map)


.. image:: https://pm4py.fit.fraunhofer.de/static/assets/images/getting_started/hnet_running_example.png

*Figure 9: Process Map (HM-based) discovered based on the running example event data set.*


Conformance Checking
------------------------------------

.. raw:: html

    <!--<iframe width="560" height="315" src="https://www.youtube.com/embed/0YNvijqX3FY" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>-->
    <a href="https://www.youtube.com/embed/0YNvijqX3FY" target="_blank" rel="noopener noreferrer">→ Watch on YouTube: pm4py tutorials - tutorial #8 conformance checking</a>

