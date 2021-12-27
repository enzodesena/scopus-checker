import csv
from document import *
from strsimpy.overlap_coefficient import OverlapCoefficient

def load_documents(csv_filename):
    my_documents = []
    with open(csv_filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Cited by'] == '':
                num_citations = 0
            else:
                 num_citations = row['Cited by']

            start_page = re.sub("[^0-9]", "", row['Page start'])
            end_page = re.sub("[^0-9]", "", row['Page end'])
            document = Document(
                row['\ufeffAuthors'],
                row['Title'],
                row['Source title'],
                row['Volume'],
                row['Issue'],
                row['Year'],
                start_page,
                end_page,
                row['References'].split('; '),
                num_citations)
            my_documents.append(document)
    return my_documents

def distance_between_strings(string_a, string_b):
    string_a = string_a.lower().replace('-', '').replace(' ', '')
    string_b = string_b.lower().replace('-', '').replace(' ', '')
    sim = OverlapCoefficient(3)

    if len(string_a) <= 2 or len(string_b) <= 2 or len(string_b) < len(string_a) * 0.6:
        # The check len(string_b) < len(string_a) * 0.8 is added for cases like this:
        # string_a On the convergence of the multipole expansion method
        # string_b CEO
        # distancE: 1.0
        # Here I am assuming that string_a is the actual title and string_b is the title we are comparing to
        # The reason why the check is len(string_b) < len(string_a) * 0.8 and not the other way around
        # is that more often than not, string_b may contain the title of the proceedings/journal

        distance = 1
    else:
        distance = sim.distance(string_b, string_a)
    return distance


def is_same_document(document_a, document_b):

    distance_between_titles = distance_between_strings(document_a.title, document_b.title)
    distance_between_authors = distance_between_strings(document_a.authors, document_b.authors)
    distance_between_sources = distance_between_strings(document_a.source_title, document_b.source_title)

    if len(document_a.source_title) > 0 and len(document_b.source_title) > 0 and \
            distance_between_sources < 0.1 and \
            len(document_a.volume) > 0 and len(document_b.volume) > 0 and \
            document_a.volume == document_b.volume and \
            len(document_a.issue) > 0 and len(document_b.issue) > 0 and \
            document_a.issue == document_b.issue and \
            document_a.start_page is not None and document_b.start_page is not None and \
            document_a.start_page == document_b.start_page and \
            document_a.end_page is not None and document_b.end_page is not None and \
            document_a.end_page == document_b.end_page:
        return True

    if distance_between_titles < 0.1:
        return True
    elif distance_between_titles < 0.5 and distance_between_authors < 0.5 and distance_between_sources < 0.5:

        return True
    else:
        return False



def add_citations_to_documents(documents, citing_documents):
    for document in documents:
        document.print_data()
        document.cited_by = find_documents_citing_this_document(document, citing_documents)
        print('Num citations indicated by SCOPUS: ', document.num_citations)
        print('Num citations found in SCOPUS citing documents CSV: ', len(document.cited_by))
        if int(document.num_citations) is not len(document.cited_by):
            print('WARNING: the number listed on the documents CSV is not the same as '+\
                  'the number of citing documents found in the citations CSV. '+\
                  'This may be due to poor parsing of the citation CSV. '+\
                  'Results may be inaccurate.')
        print('----- ----- ----- ----- ----- ----- ----- ----- ----- ----- ')


def find_documents_citing_this_document(this_document, citing_documents):
    documents_citing_this_document = []

    for citing_document in citing_documents:
        for reference_in_citing_document in citing_document.references:
            if is_same_document(this_document, reference_in_citing_document):
                documents_citing_this_document.append(citing_document)
    return documents_citing_this_document




##### ##### ##### ##### ##### ##### ##### MAIN


my_scopus_documents = load_documents('data/documents.csv')
scopus_citing_documents = load_documents('data/citedby.csv')

add_citations_to_documents(my_scopus_documents, scopus_citing_documents)
