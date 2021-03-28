import platform
import os
import threading
import multiprocessing
import urllib.request as req

path_windows = r"C:\Program Files (x86)\Fractal Softworks\Starsector\mods"
# MODTHREAD is a plceholder for the actual ID of the thread
mod_thread = "https://fractalsoftworks.com/forum/index.php?topic=MODTHREAD.0"
# for the maximum number of threads to run at once
number_of_physical_cores = multiprocessing.cpu_count()


def start_windows():
    root, dirs, files = next(os.walk(path_windows))  # gets only the directoories
    print(dirs)
    for _dir in dirs:
        lst = os.listdir(os.path.join(path_windows,_dir))
        print(f"{_dir} : {lst}")
        for file in lst:
            if file.endswith(".version"):
                print(f"Mod {_dir} contains a versioning file: {file}")
                try:
                    dct = {}
                    with open(os.path.join(path_windows,_dir,file)) as f:
                        content = [lines.strip() for lines in f.readlines()]
                        print(content)
                        for l in content:
                            if l.startswith("#"):
                                # ignore comments in the file
                                pass
                            else:
                                # split everything and store in a dicttionary
                                try:
                                    k, v = l.split(":", 1)  # split just the first :
                                    v1 = v.replace("\"", "").replace(",", "")
                                    dct[k.replace("\"","")] = v1 if len(v1) else None
                                except Exception as e:
                                    pass
                        print(dct)
                        if dct["masterVersionFile"]:
                            raw_response = req.urlopen(dct["masterVersionFile"])
                            response = raw_response.read().decode("utf8")
                            print(response)
                            if dct["modThreadId"]:
                                print(mod_thread.replace("MODTHREAD", dct["modThreadId"]))
                            else:
                                print(f"Mod {_dir} doesn't specify a mod thread. Cannot be updated.")
                        else:
                            print(f"Mod {_dir} doesn't specify a master version file. Cannot compare versions.")
                except Exception as e:
                    print(f"Mod {_dir} contains an error in the versioning file.")
                    print(e)
                break
        else:
            print(f"Mod {_dir} doesn't contains a versioning file.")




def start_mac():
    pass


def start_linux():
    # from glob import glob
    # glob("/path/to/directory/*/")
    pass


if __name__ == "__main__":
    print(platform.system())
    print(number_of_physical_cores)
    if platform.system() == "Windows":
        start_windows()
    elif platform.system() == "Darwin":
        start_mac()
    elif platform.system() == "Linux":
        start_linux()
    else:
        print("OS not supported.")
