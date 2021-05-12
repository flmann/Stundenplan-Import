import re
import math
from itertools import chain
import pytz
import urllib.request
import pandas as pd
import pprint
import calendar
import uuid

from datetime import datetime, timedelta
from icalendar import vDatetime
from icalendar.cal import Calendar, Event, Timezone, TimezoneStandard, TimezoneDaylight

from typing import List

COLON = ":"
seperator = "%"
MONDAY = 0
SATURDAY = 5
SUNDAY = 6

WEEKDAYS = {
    "montag": 0,
    "dienstag": 1,
    "mittwoch": 2,
    "donnerstag": 3,
    "freitag": 4,
    "samstag": 5,
    "sonntag": 6,
}

timetable_select_url = "http://www.et.tu-dresden.de/stundenplan/stundenplan_auswahl.php"
timetable_base_url = "http://www.et.tu-dresden.de/stundenplan/stundenplan_anzeige.php?gruppe=%group%&semester=%semester%&zeit=1"
academic_year_base_url = "https://tu-dresden.de/studium/im-studium/ressourcen/dateien/studiengangsangelegenheiten/studienjahresablaufplan-%year%"

recess = ["vorlesungsfrei", "dies academicus"]


def expand_semester(sem: str) -> str:
    if sem[0:2] == "WS":
        return f"Wintersemester 20{sem[2:4]}"
    elif sem[0:2] == "SS":
        return f"Sommersemester 20{sem[2:4]}"
    else:
        print("error")
        exit()


def flip_name(name: str) -> str:
    return " ".join(name.split(', ')[::-1])


def weekdate_generator(start_date: datetime, end_date: datetime):
    delta = end_date - start_date
    for i in range(delta.days + 1):
        day = start_date + timedelta(days=i)
        if not day.weekday() == SATURDAY and not day.weekday() == SUNDAY:
            yield day


def download_timeable_overview():
    fp = urllib.request.urlopen(timetable_select_url)
    mybytes = fp.read()
    html_doc = mybytes.decode("utf-8").replace("<BR>", seperator)
    fp.close()

    match = re.findall(r"<a href=(.+?)</a>", html_doc, re.IGNORECASE)

    result = []
    if match:
        for m in match:
            group, title = re.findall(r"gruppe=(.+?) title=(.+?) target", m, re.IGNORECASE)[0]

            group = group.strip("\"")
            title = title.strip("\"")

            if not title == "":
                result.append((group, title))
    else:
        print(f"error. did not find match at url {timetable_select_url}")
        exit()

    dfs = pd.read_html(html_doc)
    dfs = [df.applymap(lambda x: x.replace(u"\xa0", u" ") if isinstance(x, str) else x) for df in dfs]

    result1 = []
    for col in dfs[1]:
        for group, title in result:
            if group.split("&")[0] in dfs[1][col][0]:
                result1.append((group, title, " ".join(dfs[1][col][0].split(" ")[0:3])))

    return result1


def download_timeable(group_selector: str, semester_selector: str) -> List[str]:
    assert (semester_selector[0:2] == "WS" and len(semester_selector) == 7) or (semester_selector[0:2] == "SS" and len(semester_selector) == 4)

    timetable_url = timetable_base_url.replace("%semester%", semester_selector).replace("%group%", group_selector)

    fp = urllib.request.urlopen(timetable_url)
    mybytes = fp.read()
    html_doc = mybytes.decode("utf-8").replace("<BR>", seperator)
    fp.close()
   
    dfs = pd.read_html(html_doc)
    dfs = [df.applymap(lambda x: x.replace(u"\xa0", u" ") if isinstance(x, str) else x) for df in dfs]

    timetable = dfs[1].values.tolist()

    index = 2

    class_list = []
    for i, row in enumerate(timetable):
        if i == 0:
            continue
        for j, cell in enumerate(row):
            if j == 0 or isinstance(cell, float):
                continue
            classes = dfs[index].values.tolist()

            for c in classes:
                lecturer, name, room, *_ = c[0].split(seperator)
                if not name in class_list:
                    class_list.append(name)
            index += 1 

    return (class_list, dfs)


def create_cal_from_classes(dfs_list, class_list: List[str], semester_selector: str):
    assert (semester_selector[0:2] == "WS" and len(semester_selector) == 7) or (semester_selector[0:2] == "SS" and len(semester_selector) == 4)

    academic_year_url = academic_year_base_url.replace("%year%", f"20{int(semester_selector[2:4]) - 1}-{int(semester_selector[2:4])}" if semester_selector[0:2] == "SS" else f"20{semester_selector[2:7].replace('/', '-')}")

    fp = urllib.request.urlopen(academic_year_url)
    mybytes = fp.read()
    html_doc2 = mybytes.decode("utf8")
    fp.close()

    academic_year = Calendar.from_ical(html_doc2)

    semester_date_spans = []
    recess_date_spans = []

    for component in academic_year.walk():
        if component.name == 'VEVENT':
            if component['summary'].startswith(expand_semester(semester_selector)):
                semester_date_spans.append((component['DTSTART'].dt, component['DTEND'].dt))

            if any(r.lower() in component['summary'].lower() for r in recess):
                recess_date_spans.append((component['DTSTART'].dt, component['DTEND'].dt))

    weekdates_semester = []

    for start_date, end_date in semester_date_spans:
        delta = end_date - start_date
        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            if not day.weekday() == SATURDAY and not day.weekday() == SUNDAY:
                weekdates_semester.append(day)

    recess_dates_semester = []

    for start_date, end_date in recess_date_spans:
        delta = end_date - start_date
        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            if not day.weekday() == SATURDAY and not day.weekday() == SUNDAY:
                recess_dates_semester.append(day)
    
    cal = Calendar()
    cal.add("version", 2.0)
    cal.add("prodid", "-//flmann.de//timetable//DE")
    cal.add('x-wr-calname', "Stundenplan")
    cal.add('x-wr-caldesc', "Stundenplan TU Dresden ET")
    cal.add('x-wr-timezone', "Europe/Berlin")
    
    tzc = Timezone()
    tzc.add('tzid', 'Europe/Berlin')
    tzc.add('x-lic-location', 'Europe/Berlin')

    tzs = TimezoneStandard()
    tzs.add('tzname', 'CET')
    tzs.add('dtstart', datetime(1970, 10, 25, 3, 0, 0))
    tzs.add('rrule', {'freq': 'yearly', 'bymonth': 10, 'byday': '-1su'})
    tzs.add('TZOFFSETFROM', timedelta(hours=2))
    tzs.add('TZOFFSETTO', timedelta(hours=1))

    tzd = TimezoneDaylight()
    tzd.add('tzname', 'CEST')
    tzd.add('dtstart', datetime(1970, 3, 29, 2, 0, 0))
    tzs.add('rrule', {'freq': 'yearly', 'bymonth': 3, 'byday': '-1su'})
    tzd.add('TZOFFSETFROM', timedelta(hours=1))
    tzd.add('TZOFFSETTO', timedelta(hours=2))

    tzc.add_component(tzs)
    tzc.add_component(tzd)
    cal.add_component(tzc)

    dates_added = set()

    for dfs in dfs_list:
        timetable = dfs[1].values.tolist()
        index = 2

        for i, row in enumerate(timetable):
            if i == 0:
                continue
            for j, cell in enumerate(row):
                if j == 0 or isinstance(cell, float):
                    continue

                time_info = timetable[i][0]
                weekday_tt = timetable[0][j]

                classes = dfs[index].values.tolist()

                for c in classes:
                    lecturer, name, room, *_ = c[0].split(seperator)
                    odd_even, time_start, time_end = time_info.split(seperator)

                    print(f"{name=} {name in class_list}")
                    
                    if not name in class_list:
                        continue

                    time_start_hour, time_start_minutes = [int(x) for x in time_start.split(COLON)]
                    time_end_hour, time_end_minutes = [int(x) for x in time_end.split(COLON)]

                    if odd_even == "1.WO":
                        week_mod = 1
                    elif odd_even == "2.WO":
                        week_mod = 0
                    else:
                        print(f"Error. Invalid odd_even identifier {odd_even}")
                        exit()

                    id = f"{c[0]}{time_info}"
                    if id in dates_added:
                        continue
                    dates_added.add(id)

                    for day in weekdates_semester:
                        _, weeknumber, weekday = day.isocalendar()
                        if not weekday - 1 == WEEKDAYS[weekday_tt.lower()]:
                            continue
                        if not weeknumber % 2 == week_mod:
                            continue
                        if any([d.day == day.day and d.month == day.day and d.year == day.year for d in recess_dates_semester]):
                            continue


                        e = Event()
                        e.add('summary', name)
                        e.add('dtstart', datetime(day.year, day.month, day.day, time_start_hour, time_start_minutes, 0, tzinfo=pytz.timezone("Europe/Berlin")))
                        e.add('dtend', datetime(day.year, day.month, day.day, time_end_hour, time_end_minutes, 0, tzinfo=pytz.timezone("Europe/Berlin")))
                        e.add('dtstamp', datetime.now())
                        e.add('uid', uuid.uuid4())
                        e.add('location', room)
                        e.add('description', f"Dozent: {flip_name(lecturer)}")

                        cal.add_component(e)

                index += 1


    return cal.to_ical().decode('utf-8').replace('\n\n', '\n').replace('\r\n', '\n')


def main():
    semester_selector = "WS20/21"
    # semester_selector = "SS20"

    group_selector = "EuiDE-9-NT1"

    assert (semester_selector[0:2] == "WS" and len(semester_selector) == 7) or (semester_selector[0:2] == "SS" and len(semester_selector) == 4)

    timetable_url = timetable_base_url.replace("%semester%", semester_selector).replace("%group%", group_selector)
    academic_year_url = academic_year_base_url.replace(
        "%year%", f"20{int(semester_selector[2:4]) - 1}-{int(semester_selector[2:4])}" if semester_selector[0:2] == "SS" else f"20{semester_selector[2:7].replace('/', '-')}")

    fp = urllib.request.urlopen(timetable_url)
    mybytes = fp.read()
    html_doc = mybytes.decode("utf-8").replace("<BR>", seperator)
    fp.close()

    fp = urllib.request.urlopen(academic_year_url)
    mybytes = fp.read()
    html_doc2 = mybytes.decode("utf8")
    fp.close()

    academic_year = Calendar.from_ical(html_doc2)

    semester_date_spans = []
    recess_date_spans = []

    for component in academic_year.walk():
        if component.name == 'VEVENT':
            if component['summary'].startswith(expand_semester(semester_selector)):
                semester_date_spans.append((component['DTSTART'].dt, component['DTEND'].dt))

            if any(r.lower() in component['summary'].lower() for r in recess):
                recess_date_spans.append((component['DTSTART'].dt, component['DTEND'].dt))

    weekdates_semester = []

    for start_date, end_date in semester_date_spans:
        delta = end_date - start_date
        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            if not day.weekday() == SATURDAY and not day.weekday() == SUNDAY:
                weekdates_semester.append(day)

    recess_dates_semester = []

    for start_date, end_date in recess_date_spans:
        delta = end_date - start_date
        for i in range(delta.days + 1):
            day = start_date + timedelta(days=i)
            if not day.weekday() == SATURDAY and not day.weekday() == SUNDAY:
                recess_dates_semester.append(day)

    dfs = pd.read_html(html_doc)
    dfs = [df.applymap(lambda x: x.replace(u"\xa0", u" ") if isinstance(x, str) else x) for df in dfs]

    timetable = dfs[1].values.tolist()

    cal = Calendar()

    index = 2

    class_list = []
    for i, row in enumerate(timetable):
        if i == 0:
            continue
        for j, cell in enumerate(row):
            if j == 0 or isinstance(cell, float):
                continue
            classes = dfs[index].values.tolist()

            for c in classes:
                print(c[0])
                lecturer, name, room, *_ = c[0].split(seperator)
                if not name in class_list:
                    class_list.append(name)
            index += 1

    print("[")
    for c in class_list:
        print(f"    \"{c}\",")
    print("]")

    index = 2

    for i, row in enumerate(timetable):
        if i == 0:
            continue
        for j, cell in enumerate(row):
            if j == 0 or isinstance(cell, float):
                continue

            time_info = timetable[i][0]
            weekday_tt = timetable[0][j]

            classes = dfs[index].values.tolist()

            for c in classes:
                lecturer, name, room, *_ = c[0].split(seperator)
                odd_even, time_start, time_end = time_info.split(seperator)

                time_start_hour, time_start_minutes = [int(x) for x in time_start.split(COLON)]
                time_end_hour, time_end_minutes = [int(x) for x in time_end.split(COLON)]

                if odd_even == "1.WO":
                    week_mod = 1
                elif odd_even == "2.WO":
                    week_mod = 0
                else:
                    print(f"Error. Invalid odd_even identifier {odd_even}")
                    exit()

                for day in weekdates_semester:
                    _, weeknumber, weekday = day.isocalendar()
                    
                    if not weekday - 1 == WEEKDAYS[weekday_tt.lower()]:
                        continue
                    if not weeknumber % 2 == week_mod:
                        continue
                    if any([d.day == day.day and d.month == day.day and d.year == day.year for d in recess_dates_semester]):
                        continue

                    e = Event()
                    e.add('summary', name)
                    e.add('dtstart', datetime(day.year, day.month, day.day, time_start_hour, time_start_minutes, 0, tzinfo=pytz.timezone("Europe/Berlin")))
                    e.add('dtstart', datetime(day.year, day.month, day.day, time_end_hour, time_end_minutes, 0, tzinfo=pytz.timezone("Europe/Berlin")))
                    e.add('location', room)
                    e.add('description', f"Dozent: {flip_name(lecturer)}")

                    cal.add_component(e)

            index += 1

    print(cal.to_ical().decode('utf-8'))

    with open('my.ics', 'w', encoding='utf-8') as f:
        f.write(cal.to_ical().decode('utf-8'))


if __name__ == "__main__":
    main()
