from comparator import *
from scholarly import scholarly
from scholarly import ProxyGenerator


##### ##### ##### ##### ##### ##### ##### MAIN

scopus_documents_filename = 'data/documents.csv'
scopus_citing_documents_filename = 'data/citedby.csv'
use_proxy = 'free' # 'free' or 'no'
author_name = 'Enzo De Sena' #
min_year = 2012


my_scopus_documents = load_documents(scopus_documents_filename)
scopus_citing_documents = load_documents(scopus_citing_documents_filename)

pg = ProxyGenerator()

if use_proxy != 'no':
    if use_proxy == 'free':
        pg.FreeProxies()
    elif use_proxy == 'luminati':
        if os.getenv("LUMINATI_USERNAME") is None or os.getenv("LUMINATI_PASSWORD") is None or os.getenv("LUMINATI_PORT") is None:
            raise SystemExit(f"{bcolors.FAIL}----> You set the proxy as 'luminati', but either LUMINATI_USERNAME, LUMINATI_PASSWORD or LUMINATI_PORT was not set in the .env file.{bcolors.ENDC}")
            exit()
        pg.Luminati(usr=os.getenv("LUMINATI_USERNAME"),passwd=os.getenv("LUMINATI_PASSWORD"),proxy_port = os.getenv("LUMINATI_PORT"))
    else:
        raise SystemExit(f"{bcolors.FAIL}----> The type of proxy was not recognised; the available options are 'no', 'free' or 'luminati'.{bcolors.ENDC}")
    scholarly.use_proxy(pg)


print("----> Searching for author entries on Google Scholar corresponding to the query '"+author_name+"'")

search_query = scholarly.search_author(author_name)
while True:
    try:
        author_entry = next(search_query)
    except:
        raise SystemExit(f"{bcolors.FAIL}----> There was no Google Scholar author entry corresponding to your query.{bcolors.ENDC}")
        break

    author_entry = scholarly.fill(author_entry)

    print('Author name: \t'+author_entry['name'])
    if 'affiliation' in author_entry.keys():
        print('Affiliation: \t'+author_entry['affiliation'])
    if 'citedby' in author_entry.keys():
        print('Num citations: \t'+str(author_entry['citedby']))
    if 'hindex' in author_entry.keys():
        print('H-index: \t'+str(author_entry['hindex']))
    if 'publications' in author_entry.keys():
        print('Num documents: \t'+str(len(author_entry['publications'])))
    if 'coauthors' in author_entry.keys():
        print('Num coauthors: \t'+str(len(author_entry['coauthors'])))

    print('Is this you? (y/n)')
    user_answer = input()

    if user_answer.lower() == 'y' or user_answer.lower() == 'yes':
        print('----> You accepted the entry above')
        author = author_entry
        break
    else:
        print('----> You refused the entry above')



my_scholar_documents = []

for scholar_entry in author['publications']:
    scholar_entry_filled = scholarly.fill(scholar_entry)
    document = construct_document_from_scholar_entry(scholar_entry_filled)
    my_scholar_documents.append(document)

    print('----> Handling the following Google Scholar document:')
    document.print_data()

    if document.year < min_year:
        print('----> Skipping because the document year is before ', min_year)
        continue

    print('----> Attempting to find corresponding SCOPUS entry...')
    scopus_document = find_document_in_documents(document, my_scopus_documents)
    if scopus_document is not None:
        print('----> Entry found! See below the SCOPUS entry details:')
        scopus_document.print_data()

        print('----> Looking for citations in the SCOPUS citations document...')
        scopus_document.cited_by = find_scopus_documents_citing_this_document(scopus_document, scopus_citing_documents)
        print('Num citations indicated by SCOPUS: ', scopus_document.num_citations)
        print('Num citations found in SCOPUS citing documents CSV: ', len(scopus_document.cited_by))
        if scopus_document.num_citations is not len(scopus_document.cited_by):
            print(f"{bcolors.WARNING}----> WARNING: the number listed on the documents CSV is not the same as the number of citing documents found in the SCOPUS citations CSV. This may be due to poor parsing of the citation CSV. Results likely to be inaccurate.{bcolors.ENDC}")


        print('----> Downloading Google Scholar citations of the paper... (if this hangs here, it may be due to a slow proxy or too many requests to Google Scholar; wait or connect from a different IP/proxy.)')

        while True:
            try:
                scholar_citating_documents = scholarly.citedby(scholar_entry_filled)
                for citation in scholar_citating_documents:
                    scholar_citing_document = construct_document_from_scholar_entry(scholarly.fill(citation))
                    scopus_citing_document = find_document_in_documents(scholar_citing_document, scopus_document.cited_by)
                    if scopus_citing_document is not None:
                        print(f"----> Citation found! See below the Google Scholar entry followed by the SCOPUS entry:")
                        scholar_citing_document.print_data()
                        scopus_citing_document.print_data()
                    else:
                        print(f"{bcolors.FAIL}----> The following citation does not appear to be recorded on SCOPUS:{bcolors.ENDC}")
                        scholar_citing_document.print_data()
                break
            except Exception as e:
                print(f"{bcolors.WARNING}----> Google Scholar refused request; trying a new proxy; I am restarting for the same article, so some entries may be repeated. {bcolors.WARNING}")
                try:
                    pg.get_next_proxy()
                    scholarly.use_proxy(pg)
                except Exception as e:
                    raise SystemExit(f"{bcolors.FAIL}----> I ran out of proxies; giving up... :-( {bcolors.ENDC}")
    else:
        print(f"{bcolors.FAIL}----> It appears no SCOPUS entry is present for the paper above.{bcolors.ENDC}")
    print()
    print('----- ----- ----- ----- ----- ----- ----- ----- ----- ----- ')
    print()

print(f"All done.")
