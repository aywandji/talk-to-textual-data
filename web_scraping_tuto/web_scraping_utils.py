import os

from bs4 import BeautifulSoup
import requests


def is_number(input_str):
    """Check if input_str is a string number

    Args:
        input_str (str): input string

    Returns:
        bool: True if input_str can be parse to a number (float)
    """
    try:
        float(input_str)
        return True
    except ValueError:
        return False


def from_url_to_filename(url):
    """convert web url to a filename

    Args:
        url (str): string representing the url

    Returns:
        str: filename parsed from url
    """
    return url.split("://")[1].replace("/", "_").replace(".", "_")


def from_filename_to_url(filename):
    """Parse url from filename
    (filename obtained using from_url_to_filename method)

    Args:
        filename (str): filename to parse

    Returns:
        str: resulting url
    """
    beforecom, aftercom = filename.split("com", 1)
    beforecom = beforecom.replace("_", ".")
    aftercom = aftercom.replace("_", "/")
    return "https://" + beforecom + "com" + aftercom


def download_save_html_data(url, filename,
                            save_html_content=True):
    """Downlaod html data from url and save it at filename

    Args:
        url (str): url of data to fetch
        filename (str): file path where to save downloaded data
        save_html_content (bool, optional): If True save data,
            else just return it. Defaults to True.

    Returns:
        str: downloaded html data
    """
    if not os.path.isfile(filename):
        response = requests.get(url)
        # save html data in file
        if save_html_content:
            with open(filename, "wb") as html_file:
                html_file.write(response.content)
    else:
        print("{} already exists".format(filename))
        return None

    return response.content


def doc_string_from_html_content(html_content):
    """Parse html content and return it at string data

    Args:
        html_content (str): html data to parse

    Returns:
        str: String data extracted from html_content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    doc_html_content_soup = soup.find("div", {"id": "block-total-com-content"})
    if doc_html_content_soup is None:
        doc_html_content_soup = soup.find("main")

    stripped_strings = doc_html_content_soup.stripped_strings
    document_string = ""
    new_sentence = ""
    for doc_part in stripped_strings:
        is_uppercase_str = (doc_part[0].upper() == doc_part[0]) & (
            not is_number(doc_part[0]))
        if is_uppercase_str:  # new sentence
            if len(new_sentence.split(" ")) >= 6:
                document_string = document_string + new_sentence + ". "
            new_sentence = ""
        else:
            doc_part = " " + doc_part
        new_sentence += doc_part

    return document_string


def document_string_from_source(url_or_file_path,
                                website_html_folder="websites/total_com/",
                                save_html_content=False):
    """Get string content from url of filepath containing html data

    Args:
        url_or_file_path (str): url or filepath
        website_html_folder (str, optional): destination folder where data will be save if needed.
            Defaults to "websites/total_com/".
        save_html_content (bool, optional): If True save content. Defaults to False.

    Returns:
        str: Parsed data string
    """
    # Check input
    if os.path.isfile(url_or_file_path):
        filename = url_or_file_path
        print("Reading doc from disk ", filename)
        with open(filename, "r") as html_file:
            html_content = html_file.read()
    elif "http" in url_or_file_path:
        filename = website_html_folder + from_url_to_filename(url_or_file_path)
        html_content = download_save_html_data(url_or_file_path, filename,
                                               save_html_content=save_html_content)
    else:
        print("input source is not a valid url or existing file path")
        return None

    # Generate document string content
    document_string = doc_string_from_html_content(html_content)

    return document_string
