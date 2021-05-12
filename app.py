import os
from pprint import pprint

from PyInquirer import prompt, Separator

import tt

from typing import List
from typing import Dict

def timetable_overview_menu_generator(timeable_overview, page_size) -> Dict:
    title_temp = []
    fss_temp = []

    choice_list = []

    for group, title, fs in timeable_overview:
        if not fs in fss_temp:
            choice_list.append(Separator(fs))
            fss_temp.append(fs)
        
        if not title in title_temp:
            choice_list.append(Separator(title))
            title_temp.append(title)
        
        choice_list.append({
            "name": group.replace("&semester=", " ")
        })

    return [
        {
            'type': 'checkbox',
            'qmark': 'x',
            'message': 'Auswahl Stundenplan',
            'name': 'timetable_selection',
            'choices': choice_list,
            'validate': lambda answer: 'You must choose at least one time table.' if len(answer) == 0 else True,
            'pageSize': page_size,
        }
    ]

def timetable_class_menu_generator(class_list: List[str], page_size: int) -> Dict:

    class_list = sorted(class_list, key=lambda x: (" ".join(x.split(" ")[1:]), 0 if x.split(" ")[0].startswith("V") else 1 if x.split(" ")[0].startswith("Ü") else 2 if x.split(" ")[0].startswith("P") else 3))

    choice_list = [{"name": x} for x in class_list]

    return [
        {
            'type': 'checkbox',
            'qmark': 'x',
            'message': 'Auswahl Lehrveranstaltungen',
            'name': 'class_selection',
            'choices': choice_list,
            'validate': lambda answer: 'You must choose at least one time table.' if len(answer) == 0 else True,
            'pageSize': page_size,
        }
    ]


if __name__ == "__main__":
    tt_overview = tt.download_timeable_overview()

    page_size = os.get_terminal_size().lines

    q = timetable_overview_menu_generator(tt_overview, page_size)
    answers = prompt(q)

    # answers = {'timetable_selection': ['EuiDE-9-NT1 WS20/21', 'EuiDE-9-NT2 WS20/21']}

    class_list = []
    dfs_list = []
    semester_collectors = []

    for a in answers['timetable_selection']:
        group, semester = a.split(" ")
        print(f"Loading {group} {semester}")
        class_list_, dfs_ = tt.download_timeable(group, semester)
        class_list += class_list_
        dfs_list += [dfs_]
        semester_collectors += [semester]

    assert len(set(semester_collectors)) == 1

    q = timetable_class_menu_generator(list(set(class_list)), page_size)
    answers2 = prompt(q)
    
    # answers2 = {"class_selection": ['VW Dig.Sig.Ver. I', 'ÜW Dig.Sig.Ver. I', 'VW Dig.Sig.Ver. II', 'VW Fortg.Themen Inf.theorie', 'ÜW Fortg.Themen Inf.theorie', 'V Fund.Estim.Detc', 'Ü Fund.Estim.Detc', 'VW Konvexe Opt.', 'ÜW Konvexe Opt.', 'VW M.Lern.Sig.Ver.', 'ÜW M.Lern.Sig.Ver.', 'VW Statistik 2', 'ÜO Statistik 2']}

    print(f"selection {answers2['class_selection']}")

    cal = tt.create_cal_from_classes(dfs_list, answers2['class_selection'], semester_collectors[0])

    ics_filename = 'my.ics'

    with open(ics_filename, 'w', encoding='utf-8') as f:
        f.write(cal)

    print(f"Successfully exported to {ics_filename}")