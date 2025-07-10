import os
import json
import shutil
from stat import S_ISDIR

from SFTP_CLIENT import Sftp

# LOCAL_ROMS_DIR = 'testDir'

LOCAL_ROMS_DIR = '/run/media/deck/2962d307-d465-43ef-bc40-1334c72875ac/Emulation/roms'  # ~ will be changed for user path
LIBRARY_PATH_NAME = 'thelibrary'
LIBRARY_PATH = f'{LOCAL_ROMS_DIR}/{LIBRARY_PATH_NAME}'
EMULATION_STATION_INSTALL_DIR = '~/ES-DE'  # ~ will be changed for user path

with open('colections.json', encoding='UTF-8') as file:
    libraries = json.load(file)


def load_current_collections_remote():
    client = Sftp()
    base = 'home/Juegos/5-1 Emulators/CORE - TYPE R/collections/COMPUTERS/roms/RetroBat/roms/'
    consoles = client.list_files(base)
    not_empty = {}
    for c in consoles:
        files = client.list_files(base + c)
        if (len(files) > 0):
            roms_path = base + c
            if 'roms' in files:
                roms_path += '/roms/'
            not_empty[c] = {
                "room_path": roms_path,
                "target_key": c,
                "use_dirs": False
            }

    save_to_json('colections.json', not_empty)
    client.disconnect()


def read_files(key):
    client = Sftp()
    theLibraryPath = os.path.expanduser(LIBRARY_PATH)

    if not os.path.exists(theLibraryPath):
        os.makedirs(theLibraryPath)
    else:
        print("Library path (/roms/thelibrary) already set.")

    library_console_path = theLibraryPath + f'/{libraries[key]["target_key"]}'  # where library saves own files
    roms_console_path = LOCAL_ROMS_DIR + f'/{libraries[key]["target_key"]}'  # where rom will be downloaded

    if not os.path.exists(library_console_path):
        os.makedirs(library_console_path, exist_ok=True)
    else:
        print("Console path already exists.")

    clean_previous_files(key)

    # creates a JSON to this specific game
    roms = client.list_files_attr(libraries[key]["room_path"])
    for entry in roms:
        title = entry.filename
        remote_path = libraries[key] + '/' + title
        if S_ISDIR(entry.st_mode) and not key['use_dirs']:
            roms_expanded = client.list_files_attr(remote_path)
            for rom in roms_expanded:
                rom_name = rom.filename
                size = rom.st_size / (1024 * 1024 * 1024)
                data = {}
                data['base_remote_path'] = remote_path + '/' + rom_name
                data['base_local_path'] = roms_console_path + '/' + rom_name
                os.makedirs(f'{library_console_path}/{title}', exist_ok=True)
                save_to_json(f'{library_console_path}/{title}/{rom_name}_{size:.2f}_GB.json', data)

        else:
            size = entry.st_size / (1024 * 1024 * 1024)
            data = {}
            data['base_remote_path'] = remote_path
            data['base_local_path'] = roms_console_path + '/' + title
            save_to_json(f'{library_console_path}/{title}_{size:.2f}_GB.json', data)

    client.disconnect()


def save_to_json(path, data):
    with open(path, 'w', encoding='UTF-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def clean_previous_files(key):
    theLibraryPath = os.path.expanduser(LIBRARY_PATH)
    console_library_Path = theLibraryPath + f'/{key}'
    files = os.listdir(console_library_Path)
    delete = []
    delete_dir = []
    for f in files:
        if '.json' in f:
            delete.append(f)
        elif S_ISDIR(os.stat(console_library_Path + '/' + f).st_mode):
            delete_dir.append(f)
    for d in delete:
        os.remove(console_library_Path + '/' + d)
    for d in delete_dir:
        shutil.rmtree(console_library_Path + '/' + d)


def addLibrary():
    xmlPath = os.path.expanduser(f'{EMULATION_STATION_INSTALL_DIR}/custom_systems/es_systems.xml')
    script_dir = os.path.expanduser(f'{EMULATION_STATION_INSTALL_DIR}/CustomDownloadScript')
    with open(xmlPath, 'r') as xml_file:
        xml_content = xml_file.read()
    # print(xml_content)

    libraryContent = f"""  <system>
    <name>Library</name>
    <fullname>The Library</fullname>
    <path>%ROMPATH%/{LIBRARY_PATH_NAME}</path>
    <extension>.json</extension>
    <command>/usr/bin/python3 {script_dir}/download_game.py %ROM%</command>
    <theme>library</theme>
  </system>
"""

    libraryContent = libraryContent.replace('~', os.path.expanduser('~'))

    startTag = xml_content.find('<systemList>')
    endTag = xml_content.find('</systemList>')

    if libraryContent not in xml_content:
        # -1 means string was not found. str.find(), str.index(), str.rfind() returns -1 if substring or character is not found
        if startTag != -1 and endTag != -1:
            xml_content_modified = xml_content[:endTag] + libraryContent + xml_content[endTag:]
            # print(xml_content_modified)

            with open(xmlPath, 'w') as xml_file:
                xml_file.write(xml_content_modified)
        else:
            print("<systemList> and </systemList> tags were not found.")
    else:
        print("Library is already added to es_systems.xml.")

    # copy Scrips
    os.makedirs(script_dir, exist_ok=True)

    shutil.copy2('download_game.py', f'{script_dir}/download_game.py')
    shutil.copy2('SFTP_CLIENT.py', f'{script_dir}/SFTP_CLIENT.py')
    shutil.copy2('config.py', f'{script_dir}/config.py')


# addLibrary()
# load_current_collections_remote()

for key in libraries.keys():
    read_files(key)
