import os
import plistlib
import sqlite3
from liveProgress import LiveProgress

class Utils():

    @classmethod
    def find_backups(cls, rootdir: str, stop_after_first_result: bool = False):

        if not rootdir or not os.path.isdir(rootdir):

            raise NotADirectoryError("Provided rootdir does not exist or is not a directory")   

        backup_required_files = [ "Manifest.plist", "Info.plist", "Status.plist", "Manifest.db" ]

        backups = {}

        oswalk_ref = cls.create_oswalk_progress_bar_ref(rootdir = rootdir)

        progress_total = list( oswalk_ref.keys() )[0]
        
        dirs_list_in_rootdir = list( oswalk_ref[progress_total] )
                    
        progress_bar = LiveProgress(live_progress_type = "bar", text = "Researching backups ...", progress_total = progress_total)
        progress_bar.start()

        # Start researching
        for path, dirnames, filenames in os.walk(rootdir, followlinks = False):

            count = 0
            do_break = False

            for file in backup_required_files: 

                if file in filenames:
                    count += 1

                # When found a backup folder
                if count == 4:

                    udid = path.split('/')[-1]
                    backups[udid] = path.replace('/' + udid, '')

                    if stop_after_first_result:
                        do_break = True

            if do_break:
                break

            if path in dirs_list_in_rootdir:
                progress_bar.current_progress += 1                
          
        progress_bar.current_progress = progress_total
        progress_bar.join()

        return backups


    @staticmethod
    def create_oswalk_progress_bar_ref(rootdir: str):

        dirs_list = []
        dct = {}

        number_dirs = 0

        for dir in os.listdir(rootdir):

            if os.path.isdir(os.path.join(rootdir, dir)):

                dirs_list.append(os.path.join(rootdir, dir))
                number_dirs += 1

        dct[number_dirs] = dirs_list

        return dct



    @classmethod
    def load_plist(cls, file: str):

        try:
            with open(file, "rb") as file:

                return plistlib.load(file)

        except FileNotFoundError as e:
            print(e)

        except OSError as e:
            print(e)



    @classmethod
    def db_execute(self, db_file: str, query: str):
        
        try:
            db = sqlite3.connect(db_file)
            db.row_factory = sqlite3.Row

            result = db.cursor().execute(query).fetchall()
            
            return result

        except Exception as e:
            print(e)
        
        finally:
            db.close()
