import os
import platform
import sqlite3
import NSKeyedUnArchiver
from click import FileError
from liveProgress import LiveProgress
from utils import Utils

_os_based_backups_rootdir =  { 
        "Darwin" : "~/Library/Application Support/MobileSync/Backup", 
        "Windows" : "%HOME%\Apple Computer\MobileSync\Backup"
}

_plists_list = { 
    'manifest' : 'Manifest.plist',
    'status' : 'Status.plist',
    'info' : 'Info.plist'
}

class iExtract(object):

    _backups_rootdir = None
    _backup_dir = None

    def __init__(self, udid: str, backups_rootdir: str = None):    

        self.udid = udid
        self.backups_rootdir = backups_rootdir

        self.backup_dir = os.path.join(self._backups_rootdir, self.udid)

        iExtract._backups_rootdir = self.backups_rootdir
        iExtract._backup_dir = self.backup_dir

        # Plist files
        self.manifest = self.get_manifest_plist(self.backup_dir)
        self.status = self.get_status_plist(self.backup_dir)
        self.info = self.get_info_plist(self.backup_dir)

        self.manifestDB = {}



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



    @classmethod
    def get_os_based_backups_rootdir(cls):

        o_s = platform.system()

        if o_s == "Linux":

            raise OSError("Linux detected, a provided rootdir is required.")

        # Try to get the OS default rootdir
        try: 
            return os.path.expanduser(os.path.expandvars(_os_based_backups_rootdir[o_s]))

        except:
            raise FileNotFoundError("Backups rootdir OS based NOT FOUND")



    @classmethod
    def get_manifest_plist(cls, backup_dir: str = None):

        if backup_dir is None:
                
            dir = cls._backup_dir

            if dir is None:
                raise AttributeError("Backup dir required")

        else:
            dir = os.path.expanduser(os.path.expandvars(backup_dir))

        file  = os.path.join(dir, _plists_list['manifest'])
            
        return Utils.load_plist(file)


    @classmethod
    def get_status_plist(cls, backup_dir: str = None):

        if backup_dir is None:
            
            dir = cls._backup_dir

            if dir is None:
                raise AttributeError("Backup dir required")

        else:
            dir = os.path.expanduser(os.path.expandvars(backup_dir))
        
        file = os.path.join(dir, _plists_list['status'])
            
        return Utils.load_plist(file)


    @classmethod
    def get_info_plist(cls, backup_dir: str = None):

        if backup_dir is None:
                
            dir = cls._backup_dir

            if dir is None:
                raise AttributeError("Backup dir required")

        else:
            dir = os.path.expanduser(os.path.expandvars(backup_dir))

        file = os.path.join(dir, _plists_list['info'])
        
        return Utils.load_plist(file)



    @classmethod
    def get_infos(cls, backup_dir: str = None):

        if backup_dir is None:
            
            dir = cls._backup_dir

            if dir is None:
                raise AttributeError("Backup dir required")

        else:
            dir = os.path.expanduser(os.path.expandvars(backup_dir))

        manifest = cls.get_manifest_plist(dir)
        status = cls.get_status_plist(dir)

        date = status["Date"].strftime("%m/%d/%Y, %H:%M:%S")
    
        backup_infos = {

            "UUID" : status["UUID"],
            "Date" : date,
            "Full" : status["IsFullBackup"],
            "Encrypted" : manifest["IsEncrypted"],
            "RootDir" : os.path.dirname(dir),
            "FullPath" : dir
        }

        device_infos = {

            "UDID" : manifest["Lockdown"]["UniqueDeviceID"],
            "Device name" :  manifest["Lockdown"]["DeviceName"],
            "IOS version" : manifest["Lockdown"]["ProductVersion"],
            "Passcode set" : manifest["WasPasscodeSet"],  
            "Domain version" : manifest["SystemDomainsVersion"],
            "Serial number" : manifest["Lockdown"]["SerialNumber"]
        } 

        return [ backup_infos, device_infos ]



    @classmethod
    def search_available_backups(cls, backup_rootdir: str = None):

        if backup_rootdir is None: 

            if cls._backups_rootdir is None: 

                rootdir = cls.get_os_based_backups_rootdir()
            
            else:
                rootdir = cls._backups_rootdir
        else:
            rootdir = os.path.expanduser(os.path.expandvars(backup_rootdir))

        bkp = Utils.find_backups(rootdir)

        backups = []

        for udid in bkp.keys():

            rootdir = bkp[udid]
            backup_dir = os.path.join(rootdir, udid)
            
            infos = cls.get_infos(backup_dir)

            backups.append(infos[0])

        return backups


    @classmethod
    def load_files(cls, backup_dir: str = None):

        if backup_dir is None:
            
            dir = cls._backup_dir

            if dir is None:
                raise AttributeError("Backup dir required")

        else:
            dir = os.path.expanduser(os.path.expandvars(backup_dir))
        
        manifestDB = os.path.join(dir, "Manifest.db")

        print(manifestDB)

        if os.path.isfile(manifestDB):

            try:
                db = sqlite3.connect(manifestDB)
                db.row_factory = sqlite3.Row

                files = db.cursor().execute(f"SELECT * FROM Files ORDER BY domain, relativePath").fetchall()
                
            except:
                raise FileError("Encrypted Manifest.db")

        progress_total = len(files)

        progress_bar = LiveProgress(live_progress_type = "bar", text_progress_bar = "Extracting backup files... ", progress_total = progress_total)
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


