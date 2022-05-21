import os
import plistlib
import sqlite3
from liveProgress import LiveProgress

class Utils():

    @classmethod
    def find(cls, search_from: str, target: list, stop_after_first_result: bool = False, use_progress_bar: bool = True):

        if not search_from or not os.path.isdir(search_from):

            raise NotADirectoryError("Provided search fir does not exist or is not a directory")   

        result = []

        oswalk_ref = cls.create_oswalk_progress_bar_ref(search_from = search_from)

        progress_total = list(oswalk_ref.keys())[0]
        
        dirs_list_in_search_from = list(oswalk_ref[progress_total])
                    
        progress_bar = LiveProgress(live_progress_type = "bar", text = "Researching ...", progress_total = progress_total)

        number_target = len(target)

        if use_progress_bar:
            progress_bar.start()

        for path, dirnames, filenames in os.walk(search_from, followlinks = False):

            count = 0
            do_break = False

            for file in target: 

                if file in filenames:
                    count += 1

                # When one or all pattern in a folder
                if count == number_target:

                    result.append(path)

                    if stop_after_first_result:
                        do_break = True

            if do_break:
                break

            if path in dirs_list_in_search_from:
                progress_bar.current_progress += 1                
          
        progress_bar.current_progress = progress_total
        
        if use_progress_bar: 
            progress_bar.join()

        return result



    @staticmethod
    def create_oswalk_progress_bar_ref(search_from: str):

        dirs_list = []
        dct = {}

        number_dirs = 0

        for dir in os.listdir(search_from):

            if os.path.isdir(os.path.join(search_from, dir)):

                dirs_list.append(os.path.join(search_from, dir))
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
    def db_execute(self, db_file: str, query: str, mode_row: bool = True, fetchall: bool = True):
        
        try:
            db = sqlite3.connect(db_file)

            if mode_row:
                db.row_factory = sqlite3.Row

            if fetchall:
                result = db.cursor().execute(query).fetchall()

            else:
                result = db.cursor().execute(query).fetchone()
            
            return result

        except Exception as e:
            print(e)
        
        finally:
            db.close()
