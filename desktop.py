"""Moonlight desktop client. Standard-library UI; entirely offline."""
import concurrent.futures
import datetime as dt
import json
import math
from pathlib import Path
import queue
import random
import sys
import re
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

BASE = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
sys.path.insert(0, str(BASE / 'app/src/main/python'))
import moon

BG, PANEL, TEXT, MUTED, GOLD = '#080f20', '#14213a', '#edf0f6', '#afbed6', '#e4cd99'


def local_time(epoch):
    return dt.datetime.fromtimestamp(epoch / 1000, dt.timezone.utc).astimezone().strftime('%a, %d %b %Y · %H:%M %Z (UTC%z)')


class Moonlight:
    def __init__(self, root):
        self.root = root
        root.title('Moonlight')
        root.geometry('1000x820')
        root.minsize(640, 650)
        root.configure(bg=BG)
        self.live, self.request, self.result = True, 0, None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.answers = queue.Queue()
        self.closed = False
        self.fraction, self.waxing = 0, True
        self.build_menu()
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TButton', background=PANEL, foreground=TEXT, padding=10, borderwidth=0)
        style.map('TButton', background=[('active', '#283b5c')])
        style.configure('TEntry', fieldbackground=PANEL, foreground=TEXT, padding=8)
        self.sky = tk.Canvas(root, bg=BG, highlightthickness=0, height=310)
        self.sky.pack(fill='x')
        self.sky.bind('<Configure>', lambda e: self.draw_sky())
        self.phase = self.label('Looking up…', 26, GOLD)
        self.lit = self.label('', 15)
        self.instant = self.label('', 10, MUTED)
        self.status = self.label('', 10, MUTED)
        controls = tk.Frame(root, bg=BG)
        controls.pack(pady=12)
        ttk.Button(controls, text='← Day', command=lambda: self.step(-1)).pack(side='left', padx=4)
        ttk.Button(controls, text='Now', command=self.now).pack(side='left', padx=4)
        self.date_entry = ttk.Entry(controls, width=12, font=('Segoe UI', 11))
        self.date_entry.pack(side='left', padx=8)
        self.date_entry.bind('<Return>', lambda e: self.choose_date())
        ttk.Button(controls, text='Go to date', command=self.choose_date).pack(side='left', padx=4)
        ttk.Button(controls, text='Day →', command=lambda: self.step(1)).pack(side='left', padx=4)
        self.label('YYYY-MM-DD · Date selections show local noon', 10, MUTED)
        self.label('UPCOMING NEW & FULL MOONS', 11, GOLD).pack_configure(pady=(15, 6))
        event_frame = tk.Frame(root, bg=BG)
        event_frame.pack(fill='both', expand=True, padx=40)
        self.events = tk.Text(event_frame, bg=PANEL, fg=TEXT, font=('Segoe UI', 12), wrap='word',
                              height=7, borderwidth=0, padx=20, pady=14, state='disabled')
        scroll = ttk.Scrollbar(event_frame, command=self.events.yview)
        self.events.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.events.pack(fill='both', expand=True)
        self.label('Free means free. No ads. No tracking. No account.', 11, MUTED).pack_configure(pady=14)
        self.selected = dt.datetime.now().timestamp() * 1000
        self.refresh()
        root.after(100, self.poll)
        root.after(60000, self.tick)
        root.protocol('WM_DELETE_WINDOW', self.close)

    def label(self, value, size, color=TEXT):
        label = tk.Label(self.root, text=value, bg=BG, fg=color, font=('Segoe UI', size), wraplength=920)
        label.pack(pady=2)
        return label

    def build_menu(self):
        bar = tk.Menu(self.root)
        tools = tk.Menu(bar, tearoff=False)
        tools.add_command(label='Return to now', command=self.now, accelerator='Ctrl+N')
        tools.add_command(label='Go to date', command=lambda: self.date_entry.focus_set())
        tools.add_command(label='Copy moon details & events', command=self.copy, accelerator='Ctrl+C')
        tools.add_separator()
        tools.add_command(label='Exit', command=self.close)
        bar.add_cascade(label='Tools', menu=tools)
        help_menu = tk.Menu(bar, tearoff=False)
        help_menu.add_command(label='About Moonlight', command=lambda: self.info('About Moonlight',
            'Moonlight 0.2.1\nCreated by Kaotick Jay.\n\nA free, offline window to the Moon. Current phase, illumination, date exploration and upcoming new and full moons.\n\nFree means free. No ads, subscriptions, accounts or tradeoffs. See Credits & licenses for attribution.\n\nOptional support:\nhttps://github.com/sponsors/kaotickj\nhttps://www.patreon.com/KaotickJay\nhttps://paypal.me/kaotickj\n\nSupport links open your browser; third-party privacy policies apply.'))
        help_menu.add_command(label='Privacy — free means free', command=lambda: self.info('Free means free',
            'No advertising. No telemetry. No tracking. No account or email address required. Nothing collected, sold or shared.\n\nAll calculations happen on your device. No network calls, location access or background services. Dates use your device clock and time zone.\n\nCopy details writes only to your clipboard when you choose it. The app does not read your clipboard.'))
        help_menu.add_command(label='Credits & licenses', command=lambda: self.info('Credits & licenses',
            (BASE / 'CREDITS.txt').read_text(encoding='utf-8')))
        help_menu.add_command(label='Reading the Moon', command=lambda: self.info('Reading the Moon',
            'Illumination is the sunlit fraction of the lunar disk. Phase names describe the nearest of eight sectors; a Full Moon label does not mean the exact event instant.\n\nThe cratered illustration is decorative: waxing is lit on the right. It does not show your local sky orientation, libration or eclipse darkening.\n\nDates show local noon. Now updates each minute. Event times use the device time zone at each event. Supported dates: 2001–2100. Selected NASA reference events agree within two minutes; this is not a guarantee across the full range.'))
        help_menu.add_command(label='Support Kaotick Jay (optional)', command=lambda: self.info('Support Kaotick Jay', 'Optional support for Kaotick Jay. Moonlight stays completely free; donations unlock nothing.\n\nGitHub Sponsors: https://github.com/sponsors/kaotickj\nPatreon: https://www.patreon.com/KaotickJay\nPayPal: https://paypal.me/kaotickj\n\nLinks open your browser. Those services have their own privacy policies.'))
        bar.add_cascade(label='Explore & About', menu=help_menu)
        self.root.config(menu=bar)
        self.root.bind('<Control-n>', lambda e: self.now())
        self.root.bind('<Control-c>', self.copy_shortcut)

    def copy_shortcut(self, event):
        if isinstance(event.widget, (tk.Entry, ttk.Entry, tk.Text)):
            return
        self.copy()
        return 'break'

    def info(self, title, text):
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry('650x500')
        window.configure(bg=BG)
        frame = tk.Frame(window, bg=BG)
        frame.pack(fill='both', expand=True, padx=18, pady=18)
        body = tk.Text(frame, wrap='word', bg=PANEL, fg=TEXT, padx=18, pady=18,
                       font=('Segoe UI', 12), borderwidth=0)
        scrollbar = ttk.Scrollbar(frame, command=body.yview)
        body.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        body.pack(fill='both', expand=True)
        body.insert('1.0', text)
        for index, match in enumerate(re.finditer(r'https://[^\s]+', text)):
            tag = 'link'+str(index)
            body.tag_add(tag, '1.0+'+str(match.start())+'c', '1.0+'+str(match.end())+'c')
            body.tag_config(tag, foreground=GOLD, underline=True)
            body.tag_bind(tag, '<Button-1>', lambda event, url=match.group(): webbrowser.open(url))
        body.configure(state='disabled')
        ttk.Button(window, text='Close', command=window.destroy).pack(pady=(0, 16))

    def draw_sky(self):
        c = self.sky
        c.delete('all')
        w, h = c.winfo_width(), c.winfo_height()
        for y in range(0, h, 3):
            t = y / h
            color = '#%02x%02x%02x' % (int(6+10*t), int(11+17*t), int(25+25*t))
            c.create_rectangle(0, y, w, y+3, fill=color, outline='')
        rng = random.Random(731)
        for _ in range(180):
            x, y, r = rng.random()*w, rng.random()*h, rng.choice((.5, .7, 1.1))
            c.create_oval(x-r, y-r, x+r, y+r, fill=rng.choice(('#8395b2','#b7c5dd','#dfebff')), outline='')
        c.create_text(26, 25, text='M O O N L I G H T', fill=MUTED, anchor='nw', font=('Segoe UI', 10))
        cx, cy, radius = w/2, h/2+14, min(h*.36, w*.22)
        for scale, color in ((1.18,'#17283e'),(1.12,'#20324a'),(1.06,'#2b3b51')):
            r = radius*scale
            c.create_oval(cx-r,cy-r,cx+r,cy+r,fill=color,outline='')
        c.create_oval(cx-radius,cy-radius,cx+radius,cy+radius,fill='#c9c9be',outline='')
        rng = random.Random(41)
        for _ in range(100):
            x, y = rng.uniform(-1,1), rng.uniform(-1,1)
            r = rng.uniform(.014,.07)
            if math.hypot(x,y)+r < 1:
                x, y, r = cx+x*radius, cy+y*radius, r*radius
                c.create_oval(x-r,y-r,x+r,y+r,fill='#b0b3af',outline='#d9d8cb',width=.5)
        # Mask the unilluminated side using the actual computed illuminated fraction.
        for iy in range(-math.ceil(radius), math.ceil(radius)+1):
            edge = math.sqrt(max(0, radius*radius-iy*iy))
            term = (1-2*self.fraction)*edge
            left, right = (-edge,term) if self.waxing else (-term,edge)
            if right > left:
                c.create_line(cx+left,cy+iy,cx+right,cy+iy,fill='#172235',width=1.2)

    def now(self):
        self.live = True
        self.selected = dt.datetime.now().timestamp()*1000
        self.refresh()

    def choose_date(self):
        try:
            day = dt.date.fromisoformat(self.date_entry.get().strip())
            if not dt.date(2001,1,2) <= day <= dt.date(2100,12,30):
                raise ValueError()
            self.selected = dt.datetime.combine(day, dt.time(12)).timestamp()*1000
        except (ValueError, OverflowError, OSError):
            messagebox.showerror('Choose a date', 'Enter YYYY-MM-DD between 2001-01-02 and 2100-12-30.', parent=self.root)
            return
        self.live = False
        self.refresh()

    def step(self, days):
        day = dt.datetime.fromtimestamp(self.selected/1000).date()+dt.timedelta(days=days)
        self.date_entry.delete(0, 'end')
        self.date_entry.insert(0, day.isoformat())
        self.choose_date()

    def refresh(self):
        self.request += 1
        request, stamp = self.request, self.selected
        self.status.config(text='Calculating…')
        self.result = None
        self.date_entry.delete(0, 'end')
        self.date_entry.insert(0, dt.datetime.fromtimestamp(stamp/1000).date().isoformat())
        def calculate():
            try:
                result = json.loads(moon.moon_data(stamp))
            except Exception:
                result = None
            self.answers.put((request, stamp, result))
        self.executor.submit(calculate)

    def poll(self):
        try:
            while True:
                request, stamp, result = self.answers.get_nowait()
                if request != self.request:
                    continue
                self.result = result
                if result is None:
                    self.phase.config(text='Unable to calculate')
                    self.lit.config(text='')
                    self.events.config(state='normal')
                    self.events.delete('1.0','end')
                    self.events.config(state='disabled')
                    self.fraction = 0
                    self.draw_sky()
                    self.status.config(text='Choose a date from 2001 through 2100.')
                    continue
                self.phase.config(text=result['phase_name'])
                self.lit.config(text=f"{result['illumination']*100:.1f}% illuminated")
                self.instant.config(text=('Now · ' if self.live else 'Selected date · ')+local_time(stamp))
                self.status.config(text='Event list ends at year 2100.' if len(result['events'])<4 else '')
                self.fraction, self.waxing = result['illumination'], result['waxing']
                self.draw_sky()
                self.events.config(state='normal')
                self.events.delete('1.0','end')
                self.events.insert('1.0','\n\n'.join(e['name']+'\n'+local_time(e['epoch_ms']) for e in result['events']) or 'No further events in the supported range.')
                self.events.config(state='disabled')
        except queue.Empty:
            pass
        if not self.closed:
            self.root.after(100, self.poll)

    def tick(self):
        if self.live:
            self.now()
        self.root.after(60000, self.tick)

    def copy(self):
        if self.result is None:
            return
        text = self.phase.cget('text')+'\n'+self.lit.cget('text')+'\n'+self.instant.cget('text')+'\n\n'+self.events.get('1.0','end').strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status.config(text='Copied to your clipboard')

    def close(self):
        self.closed = True
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = Moonlight(root)
    root.mainloop()
