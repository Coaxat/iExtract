import os
import platform
import NSKeyedUnArchiver
from liveProgress import LiveProgress
from utils import Utils

os_based_backups_rootdir =  { 
        "Darwin" : "~/Library/Application Support/MobileSync/Backup", 
        "Windows" : "%HOME%\Apple Computer\MobileSync\Backup"
}

_plists_dict = { 
    'manifest' : 'Manifest.plist',
    'status' : 'Status.plist',
    'info' : 'Info.plist'
}

class iExtract(object):

    _search_from_dir = None
    _backup_dir = None

    def __init__(self, udid: str, backups_rootdir: str = None):    

        self.udid = udid
        self.backups_rootdir = backups_rootdir

        self.backup_dir = os.path.join(self._backups_rootdir, self.udid)

        self.manifestDB = os.path.join(self.backup_dir, "Manifest.db")

        iExtract._search_from_dir = self.backups_rootdir
        iExtract._backup_dir = self.backup_dir

        self.manifest_plist = self.get_plist("manifest", self.backup_dir)
        self.status_plist = self.get_plist("status", self.backup_dir)
        self.info_plist = self.get_plist("info", self.backup_dir)

        self.is_encrypted = self.manifest_plist["IsEncrypted"]



    @property
    def backups_rootdir(self):
        return self._backups_rootdir


    @backups_rootdir.setter
    def backups_rootdir(self, rootdir: str):

        if rootdir is None:

            self._backups_rootdir = self.get_os_based_backups_rootdir()

        else:
            dir = os.path.expanduser(os.path.expandvars(rootdir))
            
            if os.path.isdir(dir):

                self._backups_rootdir = dir
                return
            
            raise AttributeError("Provided backup rootdir does not exist.")



    @staticmethod
    def get_os_based_backups_rootdir():

        o_s = platform.system()

        if o_s == "Linux":

            raise OSError("Linux detected, a provided rootdir is required.")

        # Try to get the OS default rootdir
        try: 
            return os.path.expanduser(os.path.expandvars(os_based_backups_rootdir[o_s]))

        except:
            raise FileNotFoundError("Backups rootdir OS based NOT FOUND")



    @classmethod
    def get_plist(cls, plist_name: str, backup_dir: str = None):

        if backup_dir is None:
                
            dir = cls._backup_dir

            if dir is None:

                raise AttributeError("Backup dir required")
        else:
            dir = os.path.expanduser(os.path.expandvars(backup_dir))

        # Allow to provide real plist name or his shortcut (eg: manifest == Manifest.plist)
        if plist_name in _plists_dict.keys():

            file  = os.path.join(dir, _plists_dict[plist_name])
        
        elif plist_name in _plists_dict.values():

            file  = os.path.join(dir, plist_name)
        
        else:
            available_plists = list(_plists_dict.values())

            raise FileNotFoundError("Provided plist does not exist.\nAvailable backup plists are: " + ', '.join(available_plists))

        return Utils.load_plist(file)



    @classmethod
    def search_available_backups(cls, search_from_dir: str = None):

        if search_from_dir is None: 

            if cls._search_from_dir is None:

                rootdir = cls.get_os_based_backups_rootdir()
            
            else:
                rootdir = cls._search_from_dir
        else:
            rootdir = os.path.expanduser(os.path.expandvars(search_from_dir))

        bkp = Utils.find_backups(rootdir)

        backups = []

        for udid in bkp.keys():

            rootdir = bkp[udid]
            backup_dir = os.path.join(rootdir, udid)
            
            manifest = cls.get_plist("manifest", backup_dir)

            date = manifest["Date"].strftime("%m/%d/%Y, %H:%M:%S")

            basic_infos = {

                "UDID" : manifest["Lockdown"]["UniqueDeviceID"],
                "Date" : date,
                "Device name" :  manifest["Lockdown"]["DeviceName"],
                "Encrypted" : manifest["IsEncrypted"],
                "Path" : backup_dir
            }

            backups.append(basic_infos)

        return backups



    def get_infos(self, infos_type: str = "all"):
        
        manifest = self.manifest_plist
        status = self.status_plist

        date = manifest["Date"].strftime("%m/%d/%Y, %H:%M:%S")

        backup_infos = {
                "Backup" : {

                    "UUID" : status["UUID"],
                    "Date" : date,
                    "Full" : status["IsFullBackup"],
                    "Encrypted" : manifest["IsEncrypted"],
                    "Rootdir" : os.path.dirname(self.backup_dir),
                    "FullPath" : self.backup_dir
            }
        }

        device_infos = {
                "Device" : {

                    "UDID" : manifest["Lockdown"]["UniqueDeviceID"],
                    "Device name" :  manifest["Lockdown"]["DeviceName"],
                    "IOS version" : manifest["Lockdown"]["ProductVersion"],
                    "Passcode set" : manifest["WasPasscodeSet"],  
                    "Domain version" : manifest["SystemDomainsVersion"],
                    "Serial number" : manifest["Lockdown"]["SerialNumber"]
            }
        } 

        list = [backup_infos, device_infos]

        if infos_type == "backup": 
            return list[0]

        elif infos_type == "device":
            return list[1]

        else:
            return list



    def get_applications(self, full_apps_list: bool = True):

        # Get the full apps list or user installed apps list
        if full_apps_list:

            apps = list(self.get_plist("manifest", self.backup_dir)['Applications'].keys())
        
        else:
            apps = self.get_plist("info", self.backup_dir)['Installed Applications']

        return apps



    def get_files(self):

        query = "SELECT * FROM Files ORDER BY domain, relativePath"

        files = Utils.db_execute(self.manifestDB, query)

        if files is None:
            return

        progress_total = len(files)

        progress_bar = LiveProgress(live_progress_type = "bar", text = "Extracting backup files... ", progress_total = progress_total)
        progress_bar.start()

        list = []

        for f in files:

            splitted = f['relativePath'].split('/')
            name = splitted[len(splitted)-1]

            fileData = {

                "Name" : name,
                "RelativePath" : f['relativePath'],
                "ID" : f['fileID'],
                "Domain" : f['domain'],
                **f
            }

            f = dict(f)

            file = NSKeyedUnArchiver.unserializeNSKeyedArchiver( f['file'] )

            fileData['file'] = file

            name = fileData['file']['RelativePath'].split('/')[-1]

            data = {
                "Name" : name,
                "Size" : fileData['file']['Size'],
                "Created" : fileData['file']['Birth'],
                "LastModified" : fileData['file']['LastModified'],
                "LastStatusChange" : fileData['file']['LastStatusChange'],
                "Mode" : fileData['file']['Mode'],
                "IsFolder" : True if fileData['file']['Size'] == 0 and 'EncryptionKey' not in fileData else False,
                "UserID" : fileData['file']['UserID'],
                "Inode" : fileData['file']['InodeNumber'],
                "File" : fileData['file']
            }

            list.append(data)

            progress_bar.current_progress += 1
        
        progress_bar.join()

        return list



    def get_domains(self):
    
        query = "SELECT DISTINCT domain FROM Files"

        result = Utils.db_execute(self.manifestDB, query)

        if result is None:
            return

        domains = []

        for domain in result:
            domains.append(domain['domain'])

        return domains





