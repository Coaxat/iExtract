from rich.progress import Progress
from rich.table import Table
from rich.live import Live
from itertools import cycle
from time import sleep
import threading

class LiveProgress(threading.Thread):
    def __init__(self, progress_total: int, live_progress_type: str = "bar", progress_table_justify: str = "center", progress_table_width: int = 140, text: int = "Progress"):    

        super().__init__()

        self.live_progress_type = live_progress_type

        self.progress_total = progress_total

        self.progress_table_justify = progress_table_justify
        self.progress_table_width = progress_table_width

        self.text = text

        self.current_progress = 0



    @property
    def live_progress_type(self):
        return self._live_progress_type


    @live_progress_type.setter
    def live_progress_type(self, live_progress: str):

        live_progress_available = ["bar", "wheel"]

        if live_progress not in live_progress_available:
            raise ValueError(str(live_progress), " does not exist")

        self._live_progress_type = live_progress
    


    @property
    def progress_total(self):
        return self._progress_total


    @progress_total.setter
    def progress_total(self, total: int):

        if not type(total) == int:
            raise TypeError(str(total), " is not an integer")
        
        self._progress_total = total



    @property
    def progress_table_justify(self):
        return self._progress_table_justify


    @progress_table_justify.setter
    def progress_table_justify(self, justify: str):

        j = ["left", "center", "right"]

        if justify not in j:
            raise ValueError(str(justify), " does not exist")
        
        self._progress_table_justify = justify



    @property
    def progress_table_width(self):
        return self._progress_table_width


    @progress_table_width.setter
    def progress_table_width(self, width: int):

        if not type(width) == int:
            raise TypeError(str(width), " is not an integer")
        
        self._progress_table_width = width



    def run(self):
        
        if self._live_progress_type == "bar":
            self.start_live_bar()
        
        elif self._live_progress_type == "wheel":
            self.start_turning_wheel()


        
    def start_live_bar(self):

        overall_progress = Progress(expand = True)
        overall_task = overall_progress.add_task(self.text, total = self._progress_total)

        progress_table = Table.grid(expand = False)
        progress_table.add_column(justify = self._progress_table_justify, width = self._progress_table_width)
        progress_table.add_row(overall_progress)

        with Live(progress_table, refresh_per_second = 10):
            
            while self.current_progress < self._progress_total:

                sleep(0.01)
                overall_progress.update(overall_task, completed = self.current_progress)


    
    def start_turning_wheel(self):

        for frame in cycle(r'-\|/-\|/'):

            if self.current_progress < self._progress_total:

                print('\r', self.text, frame, sep = '', end = '', flush = True)
                sleep(0.1)

            else:
                # Remove lastest line in console
                # Necessary to avoid unwanted wheel line after print

                cursor_up = '\x1b[1A'
                remove_line = '\x1b[2K'

                print(cursor_up + remove_line)
                break
                