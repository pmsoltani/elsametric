# My thoughts on `elsametric`

## General Info

- Project name: undecided
- Slug name: [elsametric](https://github.com/pmsoltani/elsametric)
- Short description: `elsametric` defines a set of SQLAlchemy models (classes) that help create a database for storing academic publication data.
- Initial commit: Apr. 27, 2019
- Ancestor project name: [shcopus](https://github.com/pmsoltani/shcopus)

## Motivations

The idea began when working with the [Scopus](https://www.scopus.com) website and `.csv` export files from its database. I was tasked to find academic contacts that had joint-papers with Sharif's faculty members. At first, I tried to work it out using MS Excel functions. Then I realized that some of tasks could be done better using VBA macros.

That also became problematic, as it essentially used MS Excel to store multi-dimension data into 2D Excel sheets. That year, I began learning Python, since I've been hearing about it everywhere, and so the next version of the script I wrote was in a [Jupyter](https://jupyter.org) notebook.

That script got a little bigger (and a lot messier) and was subsequently named `shcopus` (Sharif + Scopus ... silly, I know).

Then I started thinking: if I could design a database of my own and import papers data into it, I could query for whatever information I needed without depending on Scopus's somewhat slow and restrictive website.

Another motivation came from the fact that Scopus does not recognize an institution's faculty members from students and other researchers. That kind of info can be used to analyze personnel, departmental, and institutional research performance of academic institutions. I know that academic ranking systems, such as QS, THE, ARWU do such analytics to some extent.

I could build a system that integrated faculty data with publications data. In the future, the institution's ranking data from several of the ranking systems could be merged into this database to give a comprehensive portrait of the shape and performance of an institution.

My application could create profiles for individuals, departments, and whole institutions with different types of access that would show a different amount of information to the end-user.

The info provided could be used to help make better policies to improve the quality of research, recognize the needs of the community within which the institution resides, and yes, increase the rank of the institution.

## The road so far (from Supernatural)

The first step was to wrap my head around the idea of databases. I had prior exposer to SQLite, to which I had imported the data of a couple of thousand papers. But because of my lack of knowledge, the data of each paper was jammed together in 1 row of only 1 table; for example, if a paper had multiple authors they all occupied a single field and were separated using `;` character.

This initially led me to believe that I needed to use non-relational databases like MongoDB. I then discovered that relational databases (as the name suggests) can achieve this with ease. So, I began studying how to design a database. I've got several books, which I did not even look at, and read some online tutorials which were helpful. Among these, I should mention a series of articles by ?? published at [Medium](https://medium.com/) ??.

I spent a significant amount of time deciding between MySQL & PostgreSQL. In the end I landed with MySQL (which has a design tool called MySQL Workbench). I design & re-designed the database, each model more expansive than the last. The current design can be seen in fig??.

I should probably mention that some months before all these, I had started contacting the Scopus support team and requested they gave me API access. That road had its bumps too, as my institution, Sharif, was not (and isn't still) a subscriber of any Scopus product. But Scopus was generous enough to grant me access to use the API for a year, which unfortunately ended in August.

Then came the time to create a script that would get publication data from Scopus. I wanted to use the already available Python packages developed for this purpose, but since I didn't know anything about object oriented programming, I ended up writing my own module. This module, which even now exists in the repo (`custom.ipynb`), was a Jupyter Notebook.

I had trouble downloading the paper's data all at once (and it was probably never a good idea anyway) and so I ended up dividing each institution's papers by publication year and downloaded them separately. These are `JSON` files and each of them contains the publications data of at most 25 papers.

The real work was to design and implement a way of inserting these files into the MySQL database that I had created. I began developing a couple of long functions that would call MySQL and write the data, providing some checks along the way (which I will write about later in this text). That took me about a month. During that time, I kept seeing articles mentioning `ORM`s and, in particular, a package called `SQLAlchemy`.

Eventually, I learned enough to know that I should have used it from the start and save myself some time. So, back to school, I began reading online tutorials (including [this one](https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers/)) and eventually, the official `SQLAlchemy` tutorial. I created a model that would create a MySQL database like the one I designed in MySQL Workbench using Python & `SQLAlchemy`. The files I developed then are now inside the `models` directory of `elsametric`.

I then needed to use some of my previously developed functions to populate the `SQLAlchemy`-created database. The data coming from Scopus can be very dirty. Missing keys, duplicated values, you name it. My script needed to different checks and inspections. I've written a helper function called `data_inspector` which looks at the publication data and detects its problems if there are any. These problems will be logged to a file, containing the issues of all papers of each institution. This, in itself, can be the subject of academic research.

Initially, I used a lot of `if` statements. Subsequently, I learned that in Python, it is Easier to Ask Forgiveness than Permission (EAFP) than to Look Before You Leap (LBYL). I've since many of those `if` statements to `try/except` blocks (although there is still so much to do).

Inserting Scopus data was not my only task. My database design demanded to store data from 3rd-party sources as well, such as the name of the countries, different academic subjects (ASJC), journal metrics, and of course, faculty member data.

Acquiring, cleaning, and formatting the data from external sources consumed a lot of time. For example, to get Sharif's faculty data, each one's web page was examined closely to retrieve what I needed. All that resulted in a set of nicely formatted `.csv` files that my Python script, `db_populate.py` along with several helper functions (nested in the `helpers` directory of `elsametric`) uses to populate the database.

This whole experience helped me understand some essential programming routines and know that I should not just jump headfirst into coding. I know now that I should have learned `Git` and [GitHub](https://github.com) much sooner. I still don't use all their features. I've only started using GitHub's issues and pull requests only recently. I've learned some SQL commands, but that too requires more study and practice.

The project was growing and it was time for a demonstration. I knew that at some point, I needed to make a website. The _how_ I didn't know (to be honest, I still don't). I had some experience with `HTML`, `CSS`, and `JavaScript` but didn't go far. So I started reading a tutorial on Python's `flask` framework and created a server that would serve some very simple `HTML` pages. I used the awesome `amCharts 4` library to make a bar chart, a force-directed network graph, and a word cloud. I remember that I went on holiday and my friend _Amirhossein Bagheripour_ presented what I created in our office.

I always knew though, that I couldn't rely on Python to create a full website, especially when there are mature `JavaScript` frameworks such as `Node.js` and `React` around. So I started thinking that maybe I've come all this way wrong and I should have used `JavaScript` from the start. But then I learned that I could develop and serve an API using a Python webserver and render the result in a front-end `JavaScript` framework such as `React`. These subjects, however, will be discussed in texts like these hosted in the two other repositories that I am developing.

It was on October that I really got into turning `elsametric` into smaller, more managable pieces. I researched for a way of moving files (along with their histories) to another repo, and on Oct. 15, 2019, the repo `elsametric-api` was created.

For now, I think it's enough to talk about the past. The next section reviews the current state of the `elsametric` repo.

## Current state (Oct. 27, 2019)

After 5 months of continues development, let's have a look at where things stand.

Currently, the `elsametric` repo has the following structure:

```python
.
│
├── data  # all the data elsametric needs to populate a db (ignored by git)
│
├── db_design  # visual guides on the current shape of elsametric
│   ├── ER Diagram.pdf  # initial elsametric ER diagram (pdf, deprecated)
│   ├── ER Diagram.vsdx  # initial elsametric ER diagram (MS Visio, deprecated)
│   ├── map_to_db.xlsx  # how Scopus JSON keys map to db columns (MS Excel)
│   ├── Scopus DB.mwb  # current ER diagram of elsametric (MySQL Workbench)
│   ├── Scopus DB.pdf  # current ER diagram of elsametric (pdf)
│   ├── Scopus DB.png  # current ER diagram of elsametric (png)
│   ├── Scopus DB.sql  # current ER diagram of elsametric (sql commands)
│   └── scp search response json.vsdx  # mapping of Scopus JSON to db tables
│
├── elsametric  # the main package
│   │
│   ├── helpers  # functions that help analyze the data and populate the db
│   │   ├── __init__.py  # currently empty
│   │   ├── helpers.py  # functions to analyze the data (used by process.py)
│   │   └── process.py  # functions to populate the db (used by db_populate.py)
│   │
│   ├── models  # SQLAlchemy models (classes)
│   │   ├── __init__.py  # currently empty
│   │   ├── associations.py  # relationship tables
│   │   ├── author_profile.py  # author_profile table
│   │   ├── author.py  # author table plus some methods
│   │   ├── base.py  # SQLAlchemy's engine, session, declarative_base, and more
│   │   ├── country.py  # country table
│   │   ├── department_alias.py  # department_alias table, currently inactive
│   │   ├── department.py  # department table plus some methods
│   │   ├── fund.py  # fund table
│   │   ├── institution_alias.py  # institution_alias table, currently inactive
│   │   ├── institution.py  # institution table
│   │   ├── keyword_.py  # keyword_ table
│   │   ├── paper.py  # paper table plus some methods
│   │   ├── source_metric.py  # source_metric table
│   │   ├── source.py  # source table
│   │   └── subject.py  # subject table
│   │
│   └── __init__.py  # reads config.json and creates an empty db if not found
│
├── helper_scripts  # scripts for different tasks
│   ├── author_faculty_matcher.py  # matches faculty names against db records
│   ├── custom.ipynb  # uses Scopus API to download an institution's papers data
│   ├── faculties_modares.py  # faculty crawler for Tarbiat Modares University
│   ├── faculties_tehran.py  # faculty crawler for University of Tehran
│   ├── gsc_profile.py  # google scholar crawler for h-index & i10-index
│   └── helpers.py  # functions used by other scripts in the directory
│
├── .gitignore  # used by git to ignore certain files and folders
├── config.json  # configuration for elsametric (ignored by git)
├── crawlers_config.json  # configuration for the crawlers (ignored by git)
├── db_populate.py  # a script that populates the database
├── elsametric.md  # this file!
├── queries.py  # a test script (deprecated)
└── setup.py  # setuptools package instructions
```

## Current issues

There are several issues that need fixing:

- Functions inside `./elsametric/helpers` need to be refactored. They have been reviewed recently for Python's new Type Annotaions (#45), but still, they could be made simpler. Also, there are some and "TODO"s that need attention.
- The content of `./db_design` needs to be updated to the current state (v0.0.4, 9d1b556).
- The `./data` directory needs to be rid of unnecessary files and folders.
- The script `./helper_scripts/custom.ipynb` should be turned into a `.py` file with our current programming style (like #30, #31, and #32).
- The SQLAlchemy model should be refactored in a way that `elsametric` could work with both MySQL & PostgreSQL.
- Incorporate TDD (Test Driven Developement) in the code-base (#23) for a more robust application.
- Support for two-level departmental structure should be added (#40).
- Currently there is no way of updating the data already in the db. `elsametric` has only one script to "populate" the db for the first time. Since some of the publications data will change with time (such as citations count, or even the Scopus id of authors and institutions), there should be a script to use the API (if available) or exported `.csv` files from Scopus to update the db.
- At the moment, if the design of the database changes (even the type of a column) there is now way to apply that change to an already populated db. The Only way would be to create a new database from the start. This is very inefficient in terms of resource and time. `elsametric` should employ the `SQLAlchemy`'s `Alembic` package to help with the database migrations.
- It could be argued that some functions & scripts within the repo could be placed in the `elsaserver` repository, as `elsametric` should only deal with the _design_ of the database, not maintaining it. This one needs more thought and should be persuid after similar a account has been made for `elsaserver`.
- An important issue that affects every result extracted from the database, is that Scopus entities (papers, authors, institutions) can have duplicates. Scopus itself has algorithms in place to detect and merge these entities and even individuals can request for some profiles to be merged. But `elsametric` cannot and should not rely on Scopus to deal with the issue. It should have functions in place to detect similar entities and report them to the system's admin for the final decision. There can be two ways of achieving a merge of two or more entities. One way is to remove all but 1 entity and replace their relationships with the remaining primary key. The better way would be select one of these entities as the main one and register others as its alias. Whenever the info for one of these entities are requested, to information regarding all of them would be fetched.

## What to do next

To be continued.
