var selection_finished;

if ((!selection_finished == true)) {
    for (j = 1; j <= 5; j++) {
        for (i = 1; i <= 16; i++) {
            var c = 0;
            document.body.children[1].children[0].children[i].children[j].innerHTML = document.body.children[1].children[0].children[i].children[j].innerHTML.replace(
                /<\/strong><br>/g,
                function (match, it, original) {
                    return '</strong><input type=\'checkbox\' id=\'selector_' + i + '_' + j
                        + '\' ds=' + document.body.children[1].children[0].children[i].children[0].innerHTML.match(/\d?\d.DS/g)[0].replace('.DS', '')
                        + ' wo=' + document.body.children[1].children[0].children[i].children[0].innerHTML.match(/\d?\d.WO/g)[0].replace('.WO', '')
                        + ' day=' + document.body.children[1].children[0].children[0].children[j].innerHTML.match(/<strong>.*<\/strong>/g)[0].replace(/<strong>/g, '').replace(/<\/strong>/g, '')
                        + ' lv=\'' + (document.body.children[1].children[0].children[i].children[j].innerHTML.match(/<strong><nobr>.*<\/nobr><\/strong>/g) || ['', '', '', ''])[c]
                            .replace(/<strong><nobr>/g, '').replace(/<\/nobr><\/strong>/g, '').replace(/&nbsp;/g, ' ') + '\''
                        + ' location=\'' + (document.body.children[1].children[0].children[i].children[j].innerHTML.match(/<\/strong><br>.*<\/font>/g) || ['', '', '', ''])[c]
                            .replace(/<\/strong><br>/g, '').replace(/<\/font>/g, '') + '\''
                        + ' dozent=\'' + (document.body.children[1].children[0].children[i].children[j].innerHTML.match(/Helvetica'>.*<br><strong>/g) || ['', '', '', ''])[c++]
                            .replace(/Helvetica'>/g, '').replace(/<br><strong>/g, '') + '\''
                        + ' /><br>';
                });
        }
    }

    for (i = 0; i < document.getElementsByTagName('input').length; i++) {
        if (document.getElementsByTagName('input')[i].type == 'checkbox') {
            var lv_type = document.getElementsByTagName('input')[i].attributes.getNamedItem('lv').value.replace(/xA0/g, ' ').split(' ')[0];
            if (!(lv_type == 'P' || lv_type == 'PW')) {
                document.getElementsByTagName('input')[i].checked = true;
            }
        }
    }
    alert('Click on the bookmark again to download the timetable.\nPlease make sure that you have the correct lectures selected.\nThis will create approx. 200 calendar events.\nUse at your own risk!\nFor any kind of feedback feel free to contact florian.mann1@gmail.com');
    selection_finished = true;
} else {
    var download = function (filename, text) {
        var element = document.createElement('a');
        element.setAttribute('href', 'data:text/calendar;charset=utf-8,' + encodeURIComponent(text));
        element.setAttribute('download', filename);

        element.style.display = 'none';
        document.body.appendChild(element);

        element.click();

        document.body.removeChild(element);
    };

    var hashFnv32a = function (str, asString) {
        var hval = 0x811c9dc5;
        var l = 0;
        for (var i = 0, l = str.length; i < l; i++) {
            hval ^= str.charCodeAt(i);
            hval += (hval << 1) + (hval << 4) + (hval << 7) + (hval << 8) + (hval << 24);
        }
        if (asString) {
            return ('0000000' + (hval >>> 0).toString(16)).substr(-8);
        }
        return hval >>> 0;
    };

    var semester = /(?:Winter)?(?:Sommer)?semester \d{4}?(?:\/\d{4}){0,1}/g.exec(document.body.innerHTML)[0];

    var day_list = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag'];

    var dict = {};
    dict['Wintersemester 2018/2019'] = 'Mo, 08.10.2018 bis Fr, 21.12.2018 sowie Mo, 07.01.2019 bis Sa, 02.02.2019';
    dict['Sommersemester 2019'] = 'Mo, 01.04.2019 bis Fr, 07.06.2019 sowie Mo, 17.06.2019 bis Sa, 13.07.2019';
    dict['Wintersemester 2019/2020'] = 'Mo, 14.10.2019 bis Sa, 21.12.2019 sowie Mo, 06.01.2020 bis Sa, 08.02.2020';
    dict['Sommersemester 2020'] = 'Mo, 06.04.2020 bis Fr, 29.05.2020 sowie Mo, 08.06.2020 bis Sa, 18.07.2020';
    
    var dict_free = {};
    dict_free['Wintersemester 2018/2019'] = ["Reformationstag: Mi, 31.10.2018",
        "Buß- und Bettag: Mi, 21.11.2018",
        "Jahreswechsel: Sa, 22.12.2018 bis So, 06.01.2019",
        "Vorlesungsfreie Zeit: Mo, 04.02.2019 bis So, 31.03.2019",
        "Kernprüfungszeit: Mo, 04.02.2019 bis Sa, 02.03.2019"];
    dict_free['Sommersemester 2019'] = ["Ostern: Fr, 19.04.2019 bis Mo, 22.04.2019",
        "1. Mai: Mi, 01.05.2019",
        "Dies academicus: Mi, 22.05.2019",
        "Himmelfahrt: Do, 30.05.2019",
        "Pfingsten: Sa, 08.06.2019 bis So, 16.06.2019",
        "Vorlesungsfreie Zeit: Mo, 15.07.2019 bis Mo, 30.09.2019",
        "Kernprüfungszeit: Mo, 15.07.2019 bis Sa, 10.08.2019"];
    dict_free['Wintersemester 2019/2020'] = ["Reformationstag: Do, 31.10.2019",
        "Buß- und Bettag: Mi, 20.11.2019",
        "Jahreswechsel: So, 22.12.2019 bis So, 05.01.2020",
        "Vorlesungsfreie Zeit: Mo, 10.02.2020 bis Di, 31.03.2020",
        "Kernprüfungszeit: Mo, 10.02.2020 bis Sa, 07.03.2020"];
    dict_free['Sommersemester 2020'] = ["Ostern: Fr, 10.04.2020 bis Mo, 13.04.2020",
        "1. Mai: Fr, 01.05.2020",
        "Dies academicus: Mi, 13.05.2020",
        "Himmelfahrt: Do, 21.05.2020",
        "Pfingsten: Sa, 30.05.2020 bis So, 07.06.2020",
        "Vorlesungsfreie Zeit: Mo, 20.07.2020 bis Sa, 30.09.2020",
        "Kernprüfungszeit: Mo, 20.07.2020 bis Sa, 15.08.2020"];

    if (!(semester in dict)) alert('outdated. please update https://github.com/flmann/Stundenplan-Import');

    var date_range = dict[semester].replace(/\s/g, '').split('sowie').map(e => e.split('bis')).map(e => e.map(d => d.split(',')[1].split('.')).map(d => new Date([d[2], d[1], d[0]].join('-'))));
    var free_range = dict_free["Sommersemester 2019"].map(d => d.replace(/\s/g, "").split(":").splice(1).map(d => d.split("bis").map(f => f.split(",")[1].split(".")).map(f => new Date([f[2], f[1], f[0]].join("-"))))).map(d => d[0]).map(d => d.length == 1 ? d : [...Array((d[1] - d[0]) / (1000 * 60 * 60 * 24)).keys()].map(f => new Date(d[0].setDate(d[0].getDate() + f))));

    var all_mondays_A = [];
    var all_mondays_B = [];

    var next = date_range[0][0];
    while (next < date_range[date_range.length - 1][1]) {
        all_mondays_A.push(new Date(next));
        if (next.getDate() + 7 < date_range[date_range.length - 1][1]) {
            var nextB = new Date(next);
            nextB.setDate(nextB.getDate() + 7);
            all_mondays_B.push(new Date(nextB));
        }
        next.setDate(next.getDate() + 14);
    }

    var content = Array.from(document.getElementsByTagName('input')).filter(e => e.checked).map(e => {
        return (parseInt(e.attributes.getNamedItem('wo').value) == 1 ? all_mondays_A : all_mondays_B)
            .map(d => new Date(d))
            .map(d => { d.setUTCHours(Math.floor((340 + 110 * e.attributes.getNamedItem('ds').value) / 60)); return d })
            .map(d => { d.setUTCMinutes((340 + 110 * e.attributes.getNamedItem('ds').value) % 60); return d })
            .map(d => { d.setDate(d.getDate() + day_list.indexOf(e.attributes.getNamedItem('day').value)); return d })
            .map(d => ['BEGIN:VEVENT',
                'DTSTAMP:' + new Date().toISOString().replace(/[-:.]/g, '').substring(0, 15) + 'Z',
                'UID:' + e.attributes.getNamedItem('lv').value.replace(/\s/g, '') + semester.replace(/\s/g, '') + d.toISOString() + e.attributes.getNamedItem('location').value,
                'DTSTART;TZID=\'Europe/Berlin\':' + d.toISOString().replace(/[-:.]/g, '').substring(0, 15) + '',
                'DTEND;TZID=\'Europe/Berlin\':' + new Date(d.getTime() + 90 * 60000).toISOString().replace(/[-:.]/g, '').substring(0, 15) + '',
                'SUMMARY:' + e.attributes.getNamedItem('lv').value,
                'DESCRIPTION: Dozent:' + e.attributes.getNamedItem('dozent').value,
                'LOCATION:' + e.attributes.getNamedItem('location').value,
                'END:VEVENT'].join('\r\n')).join('\r\n');
    }).join('\r\n');


    var ics_beginning = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Florian Mann//TUD Stundenplan to iCal', 'X-WR-CALNAME:Stundenplan ' + semester, 'CALSCALE:GREGORIAN'].join('\r\n');

    var ics_timezone = ['BEGIN:VTIMEZONE', 'TZID:Europe/Berlin', 'TZURL:http://tzurl.org/zoneinfo-outlook/Europe/Berlin', 'X-LIC-LOCATION:Europe/Berlin', 'BEGIN:DAYLIGHT', 'TZOFFSETFROM:+0100', 'TZOFFSETTO:+0200', 'TZNAME:CEST', 'DTSTART:19700329T020000', 'RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3', 'END:DAYLIGHT', 'BEGIN:STANDARD', 'TZOFFSETFROM:+0200', 'TZOFFSETTO:+0100', 'TZNAME:CET', 'DTSTART:19701025T030000', 'RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10', 'END:STANDARD', 'END:VTIMEZONE'].join('\r\n');

    ics_end = 'END:VCALENDAR';

    download('stundenplan_' + semester.replace(/\s/g, '') + '.ics', [ics_beginning, ics_timezone, content, ics_end].join('\r\n'));

}
void (0);