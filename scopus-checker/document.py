
import re
import traceback

class Document:
    def __init__(self, authors, title, source_title, volume, issue, year, start_page, end_page, references_string, num_citations):
        self.authors = authors
        self.title = title
        self.source_title = source_title
        self.volume = volume
        self.issue = issue

        if isinstance(year, str) and len(year) > 0:
            year_without_non_digits = re.sub("[^0-9]", "", year)
            if len(year_without_non_digits) > 0:
                self.year = int(year_without_non_digits)
            else:
                self.year = None
        elif isinstance(year, int):
            self.year = year
        else:
            self.year = None

        if isinstance(start_page, str) and len(start_page) > 0:
            self.start_page = int(start_page)
        else:
            self.start_page = None

        if isinstance(end_page, str) and len(end_page) > 0:
            self.end_page = int(end_page)
        else:
            self.end_page = None

        self.references = []

        if isinstance(num_citations, str) and len(num_citations) > 0:
            self.num_citations = int(num_citations)
        else:
            self.num_citations = 0

        self.cited_by = []

        for referenced_document_string in references_string:
            try:
                document = contruct_document_from_string(referenced_document_string)
                self.references.append(document)
            except Exception as error:
                print('Error in string: ' + referenced_document_string)
                print(traceback.format_exc())
                exit()


    def print_data(self):
        print('Authors:\t '+self.authors)
        print('Title:\t\t '+self.title)
        print('Year:\t\t '+str(self.year))
        print('Source title:\t '+self.source_title)
        print('Start page:\t '+str(self.start_page))
        print('End page:\t '+str(self.end_page))
        print('Volume:\t\t '+self.volume)
        print('Issue:\t\t '+self.issue)


def get_pages(reference_string):
    if 'pp. ' in reference_string:
        pages = reference_string.split('pp. ')[1].split('.')[0]
        if pages.replace('-','').isdigit():
            # Exception: Talib, M.S., Converging VANET with vehicular cloud networks to reduce the traffic congestions: a review (2017) Int J Appl Eng Res, 12 (21), pp. 10646-10654
            start_page = pages.split('-')[0]
            end_page = pages.split('-')[1]
        else:
            start_page = ''
            end_page = ''
    else:
        start_page = ''
        end_page = ''
    return [start_page, end_page]


def get_issue_volume(reference_string):
    if '),' in reference_string:
        issue_volume = reference_string.split('),')[0].split(', ')[-1]
        volume = issue_volume.split(' (')[0]
        if volume.isdigit() and len(issue_volume.split(' (')) > 1:
            issue = issue_volume.split(' (')[1]
            if not issue.isnumeric():
                issue = ''
        else:
            issue = ''
            volume = ''
    else:
        issue = ''
        volume = ''

    if not volume.isdigit():
        volume = ''

    if not issue.isdigit():
        issue = ''

    return [issue, volume]

def get_authors_title_source_year(reference_string):
    if len(reference_string) == 0:
        return ['', '', '', '']

    if ', in:' in reference_string:
        # S. Damodaran, K. Sivalingam, Scheduling in wireless networks with multiple transmission channels, in: 7th International Conference on Network Protocols (ICNP 1999), Toronto - Canada, November 1999
        authors_title = reference_string.split(', in:')[0]
        title = authors_title.split(', ')[-1]
        authors = authors_title.split(', '+title)[0]
        source_year = reference_string.split(', in: ')[1]
        source_title = source_year.split(',')[0]
        year_attempt = source_year[-4:]
        if year_attempt.isdigit():
            year = year_attempt
        else:
            year = ''

        return [title, authors, source_title, year]
    else:
        tentative_title_format_1 = reference_string.split('(')[0].split(', ')[-1]
        if len(tentative_title_format_1) > 0:
            # E.g. (1) De Sena, E., Brookes, M., Naylor, P., van Waterschoot, T., Localization experiments with reporting by gaze: statistical framework and case study (2017) J Audio Eng Soc, 65, pp. 982-996
            title = tentative_title_format_1.rstrip()
            authors = reference_string.split(', ' + title)[0]
            source_title_attempt = reference_string.split(') ')
            if len(source_title_attempt) > 1:
                source_title = source_title_attempt[1].split(', ')[0]
            else:
                source_title = ''
        else:
            authors = reference_string.split(', (')[0]
            source_title = ''
            if len(reference_string.split(')')[1]) > 0:
                if not reference_string.split(')')[1][0] == ',':
                    # E.g. (2) Paul, L., (1936) Process of Silencing Sound Oscillations, , https://www.google.com/patents/US2043416, uS Patent

                    title = reference_string.split(')')[1].split(',')[0].strip()
                    # source_title = reference_string.split(', ')[-1]
                else:
                    # Grant, M., Boyd, S.C., (2020), http://cvxr.com/cvx, Matlab software for disciplined convex programming, version 2.1 URL:
                    title = reference_string.split('), ')[1].split(', ')[0]
            else:
                # Exception :Error in string: Lindgren, L.E., From Weighted Residual Methods to Finite Element Methods, , https://www.ltu.se/cms_fs/1.47275!/mwr_galerkin_fem.pdf, (accessed on 10 April 2019)
                title = ''


        year_attempt = re.search(r'\((.*?)\)', reference_string)

        if year_attempt is not None and year_attempt.group(1).isdigit():
            year = year_attempt.group(1)
        else:
            # Exception: Burt, P.M.S., Gerken, M., A polyphase iir adaptive filter: error surface analysis and application Proc. ICASSP 1997. 1997, IEEE Comput. Soc. Press
            year = ''

    return [title, authors, source_title, year]

def contruct_document_from_string(reference_string):
    # There seems to be two formats:
    # (1) De Sena, E., Brookes, M., Naylor, P., van Waterschoot, T., Localization experiments with reporting by gaze: statistical framework and case study (2017) J Audio Eng Soc, 65, pp. 982-996
    # (2) Paul, L., (1936) Process of Silencing Sound Oscillations, , https://www.google.com/patents/US2043416, uS Patent
    # To recognise which one is which, we check if the previous (non-space) character from the "(" symbol is a comma.
    # If it is, then it is the first format, otherwise the second

    [title, authors, source_title, year] = get_authors_title_source_year(reference_string)
    [start_page, end_page] = get_pages(reference_string)
    [issue, volume] = get_issue_volume(reference_string)

    document = Document(authors, title, source_title, volume, issue, year, start_page, end_page, '', '')

    if False:
        print('------')
        print('|'+reference_string+'|')
        document.print_data()
        print('------')

    return document


def construct_document_from_scholar_entry(scholar_entry):
    bib_entry = scholar_entry['bib']

    if 'pub_year' in bib_entry.keys():
        year = bib_entry['pub_year']
    else:
        year = ''

    if 'pages' in bib_entry.keys() and len(bib_entry['pages']) > 0:
        pages_attempt = bib_entry['pages'].split('-')
        start_page = pages_attempt[0]
        if len(pages_attempt) > 1:
            end_page = bib_entry['pages'].split('-')[1]
        else:
            end_page = ''
        start_page = re.sub("[^0-9]", "", start_page)
        end_page = re.sub("[^0-9]", "", end_page)
    else:
        start_page = ''
        end_page = ''

    if 'journal' in bib_entry.keys():
        source_title = bib_entry['journal']
    elif 'conference' in bib_entry.keys():
        source_title = bib_entry['conference']
    else:
        source_title = ''

    if 'volume' in bib_entry.keys():
        volume = bib_entry['volume']
    else:
        volume = ''

    if 'number' in bib_entry.keys():
        issue = bib_entry['number']
    else:
        issue = ''

    return Document(bib_entry['author'],
        bib_entry['title'],
        source_title,
        volume,
        issue,
        year,
        start_page,
        end_page,
        '',
        scholar_entry['num_citations'])
