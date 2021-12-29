import csv
from document import *
from strsimpy.overlap_coefficient import OverlapCoefficient
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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


def add_scopus_citations_to_documents(documents, citing_documents):
    for document in documents:
        add_scopus_citations_to_document(document, citing_documents)


def find_scopus_documents_citing_this_document(this_document, citing_documents):
    documents_citing_this_document = []

    for citing_document in citing_documents:
        for reference_in_citing_document in citing_document.references:
            if is_same_document(this_document, reference_in_citing_document):
                documents_citing_this_document.append(citing_document)
    return documents_citing_this_document


def find_document_in_documents(document, my_scopus_documents):
    for scopus_document in my_scopus_documents:
        if is_same_document(document, scopus_document):
            return scopus_document
    return None
