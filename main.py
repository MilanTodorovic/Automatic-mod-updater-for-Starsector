# Python 3.9.2
import platform
import os
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import requests
from bs4 import BeautifulSoup as bs
import zipfile

path_windows = r"C:\Program Files (x86)\Fractal Softworks\Starsector\mods\\"
JUST_UPDATES = False
# MODTHREAD is a plceholder for the actual ID of the thread
mod_thread = "https://fractalsoftworks.com/forum/index.php?topic=MODTHREAD.0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/89.0.4389.90 Safari/537.36"}
# for the maximum number of threads to run at once
number_of_physical_cores = multiprocessing.cpu_count()


def parse_local_mod_info(_dir, file):
    dct = {}
    try:
        with open(os.path.join(path_windows, _dir, file)) as f:
            content = [lines.strip() for lines in f.readlines()]
            # print(content)
            dct = parse_mod_info(content)
    except Exception as e:
        print(f"Mod {_dir} contains an error in the versioning file.")
        print(e)
    finally:
        return dct


def parse_online_mod_info(_dir, url):
    dct = {}
    try:
        response = requests.get(url, headers=HEADERS)
        # print(response)
        content = response.content.decode("utf8").split("\n")
        # print("Splitted online version ", lst1)
        dct = parse_mod_info(content)
    except Exception as e:
        print(f"{_dir} - Dead URL.")
        print(e)
    finally:
        return dct


def parse_mod_info(content):
    dct = {}
    for l in content:
        if l.startswith("#"):
            # ignore comments in the file
            pass
        else:
            # split everything and store in a dicttionary
            try:
                k, v = l.strip().split(":", 1)  # split just the first :
                position = v.find('#')
                if position:
                    # takes care of trailing comments
                    v = v[:position]
                v1 = v.replace("\"", "").replace(",", "").strip()
                dct[k.replace("\"", "").strip()] = v1 if len(v1) else None
            except Exception as e:
                pass
    return dct


def compare_mod_versions(local, online):
    if JUST_UPDATES:
        return local.get("major", "0") < online.get("major", "0") or local.get("minor", "0") < online.get("minor", "0") \
               or local.get("patch", "0") < online.get("patch", "0")
    else:
        return True


def visit_thread_url(url, _dir):
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            mod_download_url = parse_webpage(response)
            if mod_download_url:
                download_mod(mod_download_url, _dir)
                # print(mod_download_url)
            else:
                print("Couldn't find a download link on the page.")
        else:
            print(f"Request status code : {response.status_code}")
    except Exception as e:
        print("Couldn't connect to the forum.")
        print(e)


def parse_webpage(response) -> str:
    soup = bs(response.content, 'html.parser')
    # print(soup)
    github = soup.select_one("a[href*='releases/download']")
    bitbucket = soup.select_one("a[href*='/downloads']")
    patreon = soup.select_one("a[href*='https://www.patreon.com/posts/']")
    googledrive = soup.select_one("a[href*='drive.google.com']")
    print(
        f"URLs in the forum thread :\nGithub: {github}\nBitbucket: {bitbucket}\nPatreon: {patreon}\n"
        f"Google Drive: {googledrive}")
    if github:
        return github['href']
    elif bitbucket:
        return bitbucket['href']
    elif patreon:
        return parse_patreon(patreon['href'])
    elif googledrive:
        return googledrive['href']
    else:
        return ""


def parse_patreon(url):
    print("URL patreon: ", url)
    response = requests.get(url, headers=HEADERS)
    soup = bs(response.content, 'html.parser')
    return soup.select_one("a[href*='https://www.patreon.com/file?']")['href']


def download_mod(url, _dir):
    if url.endswith("7z"):
        file_name = f"{_dir}.7z"
    else:
        file_name = f"{_dir}.zip"
    save_path = os.path.join(os.path.expanduser('~'), 'Downloads\\')
    try:
        chunk_size = 128
        response = requests.get(url, stream=True)
        with open(save_path + file_name, 'wb') as fd:
            for chunk in response.iter_content(chunk_size=chunk_size):
                fd.write(chunk)
    except Exception as e:
        print(f"Something went wrong while downloading :\n{e}")
    else:
        print(f"Download successful. File '{_dir}' saved at {save_path}")
    finally:
        extract_and_replace(save_path, file_name, _dir)


def extract_and_replace(save_path, file_name, _dir):
    try:
        with zipfile.ZipFile(save_path + file_name, "r") as zip_ref:
            zip_ref.extractall(save_path)  # change to path_windows
    except Exception as e:
        print("Couldn't unzip file with zipfile. Trying winrar subprocess.")
        try:
            import subprocess
            subprocess.Popen(f"C:\\Program Files\\WinRAR\\WinRAR.exe x {save_path + file_name} {save_path}")
            print("Unzipping sucessful!")
        except Exception as e:
            print(f"Error while extracting {file_name} : {e}")
    else:
        print(f"Extraction of {file_name} successful.")
    finally:
        try:
            os.remove(save_path+file_name)
            print(f"{file_name} deleted.")
        except Exception as e:
            print(f"Soemthing went wrong while deleting {file_name} : {e}")


def do_work(_dir):
    print(f"Task started on {os.getpid()}")
    print("\n<------------------------------->")
    lst = os.listdir(os.path.join(path_windows, _dir))
    print(f"{_dir} : {lst}")
    for file in lst:
        if file.endswith(".version"):
            print(f"Mod {_dir} contains a versioning file: {file}")
            # parse the local versioning file, can be empty
            dct_local = parse_local_mod_info(_dir, file)
            # print(dct_local)
            # get and parse the online versioning file
            if dct_local.get("masterVersionFile", 0):
                # can be empty due to a dead link
                dct_online = parse_online_mod_info(_dir, dct_local["masterVersionFile"])
                if dct_online:
                    print(
                        f"\nLocal : {dct_local.get('major', '0')}.{dct_local.get('minor', '0')}."
                        f"{dct_local.get('patch', '0')}")
                    print(
                        f"Online : {dct_online.get('major', '0')}.{dct_online.get('minor', '0')}."
                        f"{dct_online.get('patch', '0')}")
                    result = compare_mod_versions(dct_local, dct_online)
                    print(f"Result : {result}")
                    if result:
                        print(f"Newer version of '{_dir}' avaibale:")
                        print(
                            f"Local : {dct_local.get('major', '0')}.{dct_local.get('minor', '0')}."
                            f"{dct_local.get('patch', '0')}")
                        print(
                            f"Online : {dct_online.get('major', '0')}.{dct_online.get('minor', '0')}."
                            f"{dct_online.get('patch', '0')}")
                    print("--------------")
            else:
                print(f"Mod {_dir} doesn't specify a master version file. Cannot compare versions.")
            # visit mod thread
            if dct_local.get("modThreadId", 0):
                url = mod_thread.replace("MODTHREAD", dct_local["modThreadId"])
                print(url)
                visit_thread_url(url, _dir)
                print("<------------------------------->")
            else:
                print(f"Mod {_dir} doesn't specify a mod thread. Cannot be updated.")
                print("<------------------------------->")
            # stops after finding the .version file
            break
        else:
            continue
    else:
        print(f"Mod {_dir} doesn't contains a versioning file.")
        print("<------------------------------->")

def start_windows():
    root, dirs, files = next(os.walk(path_windows))  # gets only the directoories
    print(f"Mods found: {dirs}")
    with ProcessPoolExecutor(max_workers=number_of_physical_cores//4) as executor:
        executor.map(do_work, dirs)


def start_mac():
    pass


def start_linux():
    # from glob import glob
    # glob("/path/to/directory/*/")
    pass


if __name__ == "__main__":
    print("This script doesn't check for the compatability between game and mod versions.")
    print(f"OS: {platform.system()}")
    print(f"CPU cores available: {number_of_physical_cores}")
    print("")
    answer = input("Would you like to download just updates (else download everything anew)? y/n")
    if answer == 'y' or answer == 'z':
        JUST_UPDATES = True
    else:
        # JUST_UPDATES is by default false
        pass
    if platform.system() == "Windows":
        start_windows()
    elif platform.system() == "Darwin":
        start_mac()
    elif platform.system() == "Linux":
        start_linux()
    else:
        print("OS not supported.")
