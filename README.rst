==========
FProgramDB
==========


FProgramDB is a Django app that uses CORDIS data available on the European Open Data Portal (EUODP -
<https://data.europa.eu/euodp>) to create a local database of Projects funded by the European Commission (EC).

It is a work-in-progress proof of concept app, not suitable for analysis by itself in its current form.

At the moment the FProgramDB app can handle data on Framework Program starting from FP6, with different degrees of
integration.

Detailed documentation will be in the "docs" directory.

Quick start
-----------

1. Add "fprogramdb" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'fprogramdb',
    ]

1bis. - OPTIONAL - Include the fprogramdb example pages, with URLconf in your project urls.py like this::

    url(r'^fprogramdb/', include('fprogramdb.urls')),

2. Run `python manage.py migrate` to create the fprogramdb models.

3. Run `python manage.py load_from_csv` to load H2020 database from cordis to the model. It prints its progress on
command line.

4. If the example webpages are enabled,start the development server server and visit
<http://127.0.0.1:8000/fprogramdb/fpH2020> to get a list of all projects loaded from H2020

5. Visit to participate in the poll.

Disclaimer
----------

This app is in no way connected to the EC.

FProgramDB is, at the moment, a proof of concept:
- It *does NOT* ship with any data from the EC CORDIS Database.
- It *does NOT* aim at representing what is really happening at a EC level in respect of Research Funding.

It does, however, allow to make use of data freely available on the <https://data.europa.eu/euodp> regarding EC Research
Funding, and for that data (downloaded at runtime) applies the © European Union, 1995-2017 and the legal notice found at
this link: <https://ec.europa.eu/info/legal-notice_en>.

Data as loaded by FProgramDB app is not suitable for analisys without preprocessing. Especially critical is the database
part related to the organizations list. In fact, the organizations list related to H2020 is quite clean, as the CE put a
great effort after FP7 in rationalizing the usage of a single PIC per institution. The list is less tidy in FP7 and even
less in  FP6, and there will be need for grouping the same institution.