from base import Session, engine, Base

from paper import Paper
from keyword_ import Keyword
from fund import Fund
from source import Source
from subject import Subject
from country import Country

Base.metadata.create_all(engine)
session = Session()

import json
import os
import io
import csv
import random
import time
import winsound
from collections import OrderedDict
from datetime import datetime

frequency = 2000  # Set Frequency (Hz)
duration = 300  # Set Duration (ms)
winsound.Beep(frequency=frequency, duration=duration)

countries = []
with io.open('Countries.csv', 'r', encoding='utf-8-sig') as csvFile:
    reader = csv.DictReader(csvFile)
    for row in reader:
       country = Country()


# p1.fund = f2
# print(p1.fund_id)

# session.add(p1)
# session.add(p2)
# session.add(f1)
# session.add(f2)

# p = session.query(Paper).filter(Paper.id==1).first()
# print(p)
# print(p.title)

# f = session.query(Fund).filter(Fund.agency_acronym=='INSF').first()
# print(f.papers)
# print(f.papers[1].title)
# session.commit()
# session.close()