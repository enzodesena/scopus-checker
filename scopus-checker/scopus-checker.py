from comparator import *
from scholarly import scholarly
from scholarly import ProxyGenerator
import sys, getopt


def usage():
    print('A python script to check which (Google Scholar) citations are missing from Scopus.')
    print('Minimal use:')
    print(sys.argv[0]+' -d <scopusdocuments> -c <scopuscitations> -a <authorname>')
    print()
    print('Additional options:')
    print("-o <outputfilename>\t\t if set will output the non-matched entries to the filename.")
    print("-p <proxy>\t\t add a proxy server; options: 'free', 'scrapterapi'; for instance:")
    print("\t-p free\t\t this will use a set of free proxies will be used;'")
    print("\t-p scraperapi\t this will use ScraperAPI as a proxy; in this case you need to add -k <yourscraperapikey>")
    print('-m <minimumyear> \t only parse paper after (and including) a given year (e.g. 2012)')
    print('-z \t\t\t if included, you will be able to choose which Google Scholar author profile to pick; if not, the first query will be chosen')
    print()
    print('This is a rather unreliable tool, and should only be used for a rough first screening. See the license for more information. ')


def print_to_console_and_file(file_stream, line):
    print(line)
    if output_stream is not None:
        output_stream.write(line + '\n')

def get_author(author_name):
    search_query = scholarly.search_author(author_name)
    while True:
        try:
            author_entry = next(search_query)
        except:
            raise SystemExit(f"{bcolors.FAIL}----> There was no Google Scholar author entry corresponding to your query.{bcolors.ENDC}")

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

        if choose_author:
            print('Is this you? (y/n)')
            user_answer = input()
            if user_answer.lower() == 'y' or user_answer.lower() == 'yes':
                print('----> You accepted the entry above')
                author = author_entry
                break
            else:
                print('----> You refused the entry above')
        else:
            author = author_entry
            break
    return author

def set_up_proxy(use_proxy, scraperapi_key):
    pg = ProxyGenerator()
    if use_proxy == 'free':
        pg.FreeProxies()
    # elif use_proxy == 'luminati':
    #     if os.getenv("LUMINATI_USERNAME") is None or os.getenv("LUMINATI_PASSWORD") is None or os.getenv("LUMINATI_PORT") is None:
    #         raise SystemExit(f"{bcolors.FAIL}----> You set the proxy as 'luminati', but either LUMINATI_USERNAME, LUMINATI_PASSWORD or LUMINATI_PORT was not set in the .env file.{bcolors.ENDC}")
    #     pg.Luminati(usr=os.getenv("LUMINATI_USERNAME"),passwd=os.getenv("LUMINATI_PASSWORD"),proxy_port = os.getenv("LUMINATI_PORT"))
    elif use_proxy == 'scraperapi':
        pg.ScraperAPI(scraperapi_key)
    else:
        raise SystemExit(f"{bcolors.FAIL}----> The type of proxy was not recognised; the available options are 'no', 'free' or 'luminati'.{bcolors.ENDC}")
    scholarly.use_proxy(pg)



#### #### #### #### #### #### #### #### #### #### #### #### #### #### #### ####
scopus_documents_filename = None
scopus_citing_documents_filename = None
output_filename = None
use_proxy = 'no' # 'no' or 'free' or 'luminati' or 'scraperapi'
author_name = None
min_year = 0
choose_author = False
scraperapi_key = None

try:
    opts, args = getopt.getopt(sys.argv[1:],"h:d:c:a:k:p:z:m:o:")
except getopt.GetoptError:
    usage()
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        usage()
        sys.exit()
    elif opt in ("-d"):
        scopus_documents_filename = arg
    elif opt in ("-c"):
        scopus_citing_documents_filename = arg
    elif opt in ("-a"):
        author_name = arg
    elif opt in ("-m"):
        min_year = int(arg)
    elif opt in ("-k"):
        scraperapi_key = arg
    elif opt in ("-z"):
        choose_author = True
    elif opt in ("-p"):
        use_proxy = arg
    elif opt in ("-o"):
        output_filename = arg

if author_name is None:
    raise SystemExit("The authos name was not recognised. See python "+sys.argv[0]+" -h for more information.")
if scopus_documents_filename is None:
    raise SystemExit("The scopus document filename was not recognised. See python "+sys.argv[0]+" -h for more information.")
if scopus_citing_documents_filename is None:
    raise SystemExit("The scopus citations filename was not recognised. See python "+sys.argv[0]+" -h for more information.")
if use_proxy == 'scraperapi' and scraperapi_key is None:
    raise SystemExit("You requested scraper API as a proxy, but did not provide a key. See python "+sys.argv[0]+" -h for more information.")


try:
    my_scopus_documents = load_documents(scopus_documents_filename)
except FileNotFoundError:
    raise SystemExit("The scopus document file was not found.")

try:
    scopus_citing_documents = load_documents(scopus_citing_documents_filename)
except FileNotFoundError:
    raise SystemExit("The scopus citations file was not found.")

if use_proxy != 'no':
    set_up_proxy(use_proxy, scraperapi_key)


output_stream = None
if output_filename is not None:
    output_stream = open(output_filename, 'w')

print("----> Searching for author entries on Google Scholar corresponding to the query '"+author_name+"'")

author = get_author(author_name)

my_scholar_documents = []
for scholar_entry in author['publications']:
    scholar_entry_filled = scholarly.fill(scholar_entry)
    scholar_document = construct_document_from_scholar_entry(scholar_entry_filled)
    my_scholar_documents.append(scholar_document)

    print_to_console_and_file(output_stream, '----- ----- ----- ----- ----- ----- ----- ----- ----- ----- ')
    print_to_console_and_file(output_stream, '----> Handling the following Google Scholar document:')
    print_to_console_and_file(output_stream, scholar_document.get_data_output())

    if scholar_document.year is not None and scholar_document.year < min_year:
        print_to_console_and_file(output_stream, '----> Skipping the document because the year is before '+str(min_year))
        continue

    print('----> Attempting to find corresponding SCOPUS entry...')
    scopus_document = find_document_in_documents(scholar_document, my_scopus_documents)
    if scopus_document is not None:
        print('----> Entry found! See below the SCOPUS entry details:')
        print(scopus_document.get_data_output())

        print('----> Looking for citations in the SCOPUS citations document...')
        scopus_document.cited_by = find_scopus_documents_citing_this_document(scopus_document, scopus_citing_documents)
        print('Num citations indicated by SCOPUS: ', scopus_document.num_citations)
        print('Num citations found in SCOPUS citing documents CSV: ', len(scopus_document.cited_by))
        if scopus_document.num_citations is not len(scopus_document.cited_by):
            print(f"{bcolors.WARNING}----> WARNING: the number listed on the documents CSV is not the same as the number of citing documents found in the SCOPUS citations CSV. This may be due to poor parsing of the citation CSV. Results likely to be inaccurate.{bcolors.ENDC}")

        if scholar_document.num_citations == 0:
            print('----> No citations for this paper. ')
            continue

        print('----> Downloading Google Scholar citations of the paper... (if this hangs here, it may be due to a slow proxy or too many requests to Google Scholar; wait or connect from a different IP/proxy.)')
        scholar_citating_documents = scholarly.citedby(scholar_entry_filled)
        for citation in scholar_citating_documents:
            scholar_citing_document = construct_document_from_scholar_entry(scholarly.fill(citation))
            scopus_citing_document = find_document_in_documents(scholar_citing_document, scopus_document.cited_by)
            if scopus_citing_document is not None:
                print(f"----> Citation found! See below the Google Scholar entry followed by the SCOPUS entry:")
                print(scholar_citing_document.get_data_output())
                print(scopus_citing_document.get_data_output())
            else:
                print_to_console_and_file(output_stream, f"{bcolors.FAIL}----> The following Google Scholar citation does not appear to be recorded on SCOPUS:{bcolors.ENDC}")
                print_to_console_and_file(output_stream, scholar_citing_document.get_data_output())
    else:
        print_to_console_and_file(output_stream, f"{bcolors.FAIL}----> It appears no SCOPUS entry is present for the paper above.{bcolors.ENDC}")

print_to_console_and_file(f"All done.")

if output_stream is not None:
    output_stream.close()
