import os
import platform
from utils import Utils

_os_based_backups_rootdir =  { 
        "Darwin" : "~/Library/Application Support/MobileSync/Backup", 
        "Windows" : "%HOME%\Apple Computer\MobileSync\Backup"
}

_root_plists = { 
    'manifest' : 'Manifest.plist',
    'status' : 'Status.plist',
    'info' : 'Info.plist',
    'manifestDB' : 'Manifest.db'
}

class iEtract(object):
    def __init__(self, udid: str, backups_rootdir: str = None):    

        self.udid = udid

        self.backups_rootdir = backups_rootdir

        self.backup_dir = os.path.join(self._backups_rootdir, self.udid)

        # Plist files
        self.manifest = self.get_manifest_plist(self.backup_dir)
        self.status = self.get_status_plist(self.backup_dir)
        self.info = self.get_info_plist(self.backup_dir)

        self.manifestDB = {}



    @property
    def backups_rootdir(self):
        return self._backups_rootdir

    @backups_rootdir.setter
    def backups_rootdir(self, rootdir):

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
    def get_manifest_plist(cls, backup_dir):

        file  = os.path.join(backup_dir, _root_plists['manifest'])
            
        return Utils.load_plist(file)


    @classmethod
    def get_status_plist(cls, backup_dir):
        
        file = os.path.join(backup_dir, _root_plists['status'])
            
        return Utils.load_plist(file)


    @classmethod
    def get_info_plist(cls, backup_dir):

        file = os.path.join(backup_dir, _root_plists['info'])
        
        return Utils.load_plist(file)

