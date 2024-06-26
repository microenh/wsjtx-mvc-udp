import os
import tkinter as tk
from tkinter import scrolledtext, ttk
from PIL import Image, ImageTk

class MainView(tk.Tk):
    """Main class"""

    def __init__(self, x, y, theme, park, shift, win32):
        super().__init__()
        # self.screenName = ':0.0'
        # if os.environ.get('DISPLAY', '') == '':
        #     os.environ.__setitem__('DISPLAY', ':0.0')
        self.setup_variables(park, shift)
        # style = ttk.Style(self)
        # style.theme_use(theme)
        self.layout(x, y, win32)

    def setup_variables(self, park, shift):
        self.rx_tx = tk.StringVar()
        self.gps_text = tk.StringVar()
        self.park = tk.StringVar(value=park)
        self.time_text = tk.StringVar()
        self.shift_text = tk.StringVar(value=shift)
    
    def layout(self, x, y, win32):
        if x > self.winfo_screenwidth():
            x = 20
        if y > self.winfo_screenheight():
            y = 20
        self.geometry(f'+{x}+{y}')
        self.resizable(False, False)
        self.title('POTA-FT8/FT4 Helper')
        logo_fn = os.path.join(os.path.dirname(__file__), "Logo.png")
        self.image = ImageTk.PhotoImage(Image.open(logo_fn))
        self.iconphoto(False, self.image)
        
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill='y')
        ttk.Label(main_frame, image=self.image).pack()
        
        bg = ttk.Frame(main_frame)
        bg.pack(padx=10)

        f = ttk.Frame(bg)
        f.pack(pady=(0,10))
        self.rx_tx_label = ttk.Label(f, textvariable=self.rx_tx)
        self.rx_tx_label.pack(anchor='center')

        cb = ttk.Frame(bg)
        cb.pack(expand=True, fill='y', pady=(0,10))
        
        self.calls_pota = self.callentrybox(cb)
        self.calls_me = self.callentrybox(cb)
        self.calls_cq = self.callentrybox(cb)

        f = ttk.Frame(bg)
        f.pack(fill='x', pady=10)
        self.park_button = ttk.Button(f, text="PARK")
        self.park_button.pack(side='left')
        e = ttk.Entry(f, textvariable=self.park)
        e.pack(side='left', fill='x', expand=True, padx=(10,0))
        ttk.Label(f, text='SHIFT').pack(side='left', padx=(10,0))
        self.shift = ttk.Combobox(f, textvariable=self.shift_text,
                         values=('','EARLY','LATE'),
                         width=8)
        self.shift.pack(side='left', padx=(10,0))
        self.shift['state'] = 'disabled' if self.park.get() == '' else 'readonly'
   
        f = ttk.Frame(bg)
        f.pack(fill='x', pady=(0,10))
        self.grid_button = ttk.Button(f, text='GRID')
        self.grid_button.pack(side='left')
        ttk.Label(f, textvariable=self.gps_text, width=20).pack(side='left', fill='x', padx=(10,0))
        self.time_button = ttk.Button(f, text='TIME')
        self.time_button.pack(side='left', padx=(10,0))
        ttk.Label(f, textvariable=self.time_text).pack(side='left', fill='x', padx=(10,0))
        
##        if win32:
##            self.time_button = ttk.Button(f)
##            self.time_button.pack(side='right', padx=(0,10))


    def callentrybox(self, frame):
        f = ttk.Frame(frame)
        f.pack(side='left', expand=True, fill='y')
        c = ttk.Treeview(f, height=10, show='tree')
        c.pack(side='left')
        vsb = ttk.Scrollbar(f, orient="vertical", command=c.yview)
        vsb.pack(expand=True, fill='y')
        
        c.configure(yscrollcommand=vsb.set)

        c['columns'] = ('SNR','Message')
        c.column('#0', width=0, stretch='no')
        c.column('SNR', width=30, stretch='no')
        c.column('Message', width=150, stretch='yes')
        return c


if __name__ == '__main__':
    m = MainView(20, 20, 'default', '', '', False)
    m.protocol('WM_DELETE_WINDOW', m.quit)
    m.mainloop()
    m.destroy()

