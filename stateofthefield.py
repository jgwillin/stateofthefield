# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 19:07:49 2018

This is a tool for finding recently published papers. It uses Beautiful Soup to parse through the HTML of
particular webpages for scientific journals where the recent publications are listed. 
Within the program, there is a search function for filtering the results.

Supported Journals include:
    - Physical Review B
    - Nature
    - arXiv


@author: jgwillingham
"""

import tkinter as tk
import urllib.request as url
from bs4 import BeautifulSoup
import webbrowser
import csv


papers_bg = 'white'
bordercolor = 'red4'
filters_bg = 'gray70'
button_color = 'gray90'
abstract_bg = 'white'
hover_color = 'gray90'
title_bg = 'gray92'
selection_bg = 'gray80'
selection_color = 'red4'

borderthickness = 12

title_font = ('Times New Roman', 12)
authors_font = ('Ariel', 8)
journals_font = ('Times New Roman', 18, 'underline')
filters_font = ('Times New Roman', 15, 'underline')
filters_list_font = ('Times New Roman', 12)

page_depth = 2 # how many pages of each Journal should be searched through

database_path = r'C:\Users\George Willingham\Repositories\stateofthefield\saved_papers_database.csv'
    


class Main(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.geometry('1800x800')
        print('\n___State of the Field___\n')
        
        container = tk.Frame(self, highlightbackground=bordercolor, highlightcolor=bordercolor, highlightthickness=borderthickness, bg=papers_bg)
        container.grid(row=0, column=0, sticky='nsew')

        self.elements = {}
        
        self.elements[Filters] = Filters(self)
        self.elements[Filters].grid(row=0, column=1, sticky='nsew')
        self.grid_columnconfigure(0, weight=8, uniform='group1')
        self.grid_columnconfigure(1, weight=5, uniform='group1')
        self.grid_rowconfigure(0, weight=1, uniform='group1')
        
        self.elements[Papers] = Papers(container, self)
        self.elements[Papers].pack(side='left', fill='both', expand=True)
        
        self.scroller = 'papers'
        self.title('State of the Field')
        self.iconbitmap(r'C:\Users\George Willingham\Documents\Code\Personal Projects\State of the Field\app-icon2.ico')
            

class Papers(tk.Canvas):
    def __init__(self, parent, root):
        tk.Canvas.__init__(self, parent, bg=papers_bg)
        self.root = root
        self.hovering = {}
        self.selection = {}

        self.scrollbar = tk.Scrollbar(self, command=self.yview)
        self.scrollbar.pack(side='left', fill='y')
        root.bind_all('<MouseWheel>', self._on_mouse_wheel)
        self.bind('<Enter>', self._scroll_papers)
        self.configure(yscrollcommand = self.scrollbar.set)
        self.bind('<Configure>', self._on_configure)
        
        
        self.frame = tk.Frame(self, bg=papers_bg)
        self.create_window((0,0), window=self.frame, anchor='nw')
        print('getting publications')
        try:
            self._get_PhysRevB_papers()
            self._get_Nature_papers()
            self._get_arXiv_papers()
            isConnected = True
        except:
            print('ERROR: Could not connect to host')
            message = tk.Label(self, text='\n\nNo Internet Connection', bg=papers_bg)
            message.pack()
            isConnected = False

        if isConnected:
            root.bind('<Button-1>', self._select_paper)
            self.row = 0
            self.labels = {}
            print('displaying publications')
            self.show_papers(self.prb_papers)
            self.show_papers(self.nat_papers)
            self.show_papers(self.arx_papers)
            self.scrollbar.tkraise()
            print('\nDONE')
    
    
    def _get_PhysRevB_papers(self):
        print('opening Physical Review B . . .')
        prb_titles = []
        prb_authors = []
        prb_links = []
        prb_pubinfo = []
        for page in [i for i in range(1, page_depth+1)]:
            print(f'\tparsing page {page} . . .')
            prb_html = url.urlopen(f'https://journals.aps.org/prb/recent?page={page}')
            self.prb = BeautifulSoup(prb_html, 'lxml')
            prb_titles += self.prb.find_all('h5', "title")
            prb_authors += self.prb.find_all('h6', "authors")
            prb_pubinfo += self.prb.find_all('h6', 'pub-info')
        prb_links = [prb_titles[i].find('a').attrs['href'] for i in range(len(prb_titles)) if '<h5 class="title">' in str(prb_titles[i])]
        prb_papers = {}
        inx = 0
        for item in prb_titles:
            if '<h5 class="title">' in str(item):
                title = item.text
                authors = prb_authors[inx].text
                link = 'https://journals.aps.org' + prb_links[inx]
                pubinfo = prb_pubinfo[inx].text
                prb_papers[title] = {
                        'title':title,
                        'authors':authors,
                        'link':link,
                        'pubinfo':pubinfo,
                        'abstract':''
                        }
                inx += 1
        self.prb_papers = prb_papers
        self.prb_papers_label = tk.Label(self.frame, text='\tPhysical Review B\n', font=journals_font, bg=papers_bg)
        
        
    def _get_arXiv_papers(self):
        print('parsing new arXiv submissions . . .')
        arx_html = url.urlopen(r'https://arxiv.org/list/cond-mat/new')
        self.arx = BeautifulSoup(arx_html, 'lxml')
        arx_titles = self.arx.find_all('div', 'list-title mathjax')
        arx_authors = self.arx.find_all('div', 'list-authors')
        arx_links = [item for item in self.arx.find_all('a') if 'href="/abs' in str(item) and 'Abstract' in str(item)]
        arx_pubinfo = [item.text for item in arx_links]
        
        arx_papers = {}
        inx = 0
        for inx in range(len(arx_titles)):
            title = arx_titles[inx].text.split(' ', 1)[1].split('\n')[0]
            authors_list = arx_authors[inx].text.split('\nAuthors:\n', 1)[1].split(', \n')
            authors_list[-1] = authors_list[-1].split('\n')[0]
            authors = ''
            for i in range(len(authors_list)):
                if i == 0:
                    authors += authors_list[i]
                elif i == len(authors_list)-1 and i != 0:
                    authors += ', and ' +authors_list[i]
                else:
                    authors += ', ' + authors_list[i]
            pubinfo = arx_pubinfo[inx]
            link = 'https://arxiv.org/abs/' + pubinfo.split(':')[1]
            arx_papers[title] = {
                      'title':title,
                      'authors':authors, 
                      'link':link, 
                      'pubinfo':pubinfo+' \u2013 Recent',
                      'abstract':''
                      }
        self.arx_papers = arx_papers
        self.arx_papers_label = tk.Label(self.frame, text='\tarXiv\n', font=journals_font, bg=papers_bg)
        
        
    def _get_Nature_papers(self):
        print('opening Nature . . .')
        nat_titles = []
        nat_authors = []
        nat_links = []
        nat_pubinfo = []
        for page_num in [i for i in range(1, page_depth+1)]:
            print(f'\tparsing page {page_num} . . .')
            nat_html = url.urlopen(f'https://www.nature.com/search?article_type=protocols%2Cresearch%2Creviews&subject=condensed-matter-physics&page={page_num}')
            nat = BeautifulSoup(nat_html, 'lxml')
            page_articles = [item for item in nat.find_all('a') if r'nature.com/articles' in str(item)]
            page_titles = [item.text for item in page_articles]
            page_papers_info = [item.text for item in nat.find_all('li') if 'author' in str(item)]
            page_links = [item.attrs['href'] for item in page_articles]
            page_authors = []
            page_pubinfo = []
            j = 0
            for i in range(len(page_papers_info)):
                if j == len(page_titles):
                    break
                if page_titles[j] in page_papers_info[i]:
                    k = i + 1
                    authors = ''
                    while 'Opens in a new window' not in page_papers_info[k]:
                        authors += page_papers_info[k]
                        k += 1
                        if k == len(page_papers_info)-6:
                            break
                    page_authors.append(authors)
                    date = page_papers_info[i].split(' | ')[1].split(page_titles[j])[0]
                    branch = page_papers_info[i].split(authors)[1].split('Rights\xa0')[0]
                    page_pubinfo.append(branch + ' \u2013 Published '+ date)
                    j += 1
            nat_titles += page_titles
            nat_authors += page_authors
            nat_links += page_links
            nat_pubinfo += page_pubinfo

        nat_papers = {}
        for i in range(len(nat_titles)):
            title = nat_titles[i]
            authors = nat_authors[i]
            pubinfo = nat_pubinfo[i]
            link = nat_links[i]
            nat_papers[title] = {
                    'title':title,
                    'authors':authors,
                    'link':link,
                    'pubinfo':pubinfo,
                    'abstract':''
                    }
        self.nat_papers = nat_papers
        self.nat_papers_label = tk.Label(self.frame, text='\tNature\n', font=journals_font, bg=papers_bg)
    

    def show_papers(self, papers):
        if papers == self.prb_papers or papers == self.root.elements[Filters].prb_hits:
            self.prb_papers_label.grid_forget()
            self.prb_papers_label.grid(row=self.row, column=1, sticky='w')    
        if papers == self.nat_papers or papers == self.root.elements[Filters].nat_hits:
            self.nat_papers_label.grid_forget()
            self.nat_papers_label.grid(row=self.row, column=1, sticky='w')
            
        if papers == self.arx_papers or papers == self.root.elements[Filters].arx_hits:
            self.arx_papers_label.grid_forget()
            self.arx_papers_label.grid(row=self.row, column=1, sticky='w') 
                
        self.row += 1
        link_callbacks = {}
        abstract_callbacks = {}
        hover_callbacks = {}
        for paper in papers.keys():
            title = papers[paper]['title']
            authors = papers[paper]['authors']
            link = papers[paper]['link']
            pubinfo = papers[paper]['pubinfo']
            def link_callback(event, link=link):
                webbrowser.open_new(link)
            link_callbacks[title] = link_callback
            def abstract_callback(papers=papers, paper=paper):
                self._get_abstract(papers, paper)
            abstract_callbacks[title] = abstract_callback
            self.labels[title+'-box'] = tk.Label(self.frame, bg=papers_bg, width=200)
            self.labels[title+'-box'].grid(row=self.row, column=1, rowspan=3, columnspan=3, pady=(0, 5), sticky='nsew')
            self.labels[title] = tk.Label(self.frame, text=title, font=title_font, bg=title_bg, cursor='hand2', wraplength=1200, justify='left')
            self.labels[title].bind('<Button-1>', link_callbacks[title])
            self.labels[title].grid(row=self.row, column=1, padx=40, pady=(5, 0), sticky='w')
            self.row += 1
            self.labels[title+'-authors'] = tk.Label(self.frame, text=authors, font=authors_font, bg=papers_bg, wraplength=1200, justify='left', state='normal', activebackground='red4')
            self.labels[title+'-authors'].grid(row=self.row, column=1, padx=100, sticky='w')
            self.row +=1
            self.labels[title+'-pubinfo'] = tk.Label(self.frame, text=pubinfo+'\n', font=authors_font, bg=papers_bg, wraplength=1200, justify='left')
            self.labels[title+'-pubinfo'].grid(row=self.row, column=1, padx=100, sticky='w')
            self.labels[title+'-get_abstract'] = tk.Button(self.frame, text='Abstract', command=abstract_callbacks[title], bg=button_color, font=authors_font)
            self.labels[title+'-get_abstract'].grid(row=self.row, column=1, padx=(200, 0), pady=(0, 35), sticky='n')
            self.row += 1
            if self.selection == papers[paper]:
                self.labels[title].config(bg=selection_bg)
                self.labels[title+'-authors'].config(bg=selection_bg)
                self.labels[title+'-pubinfo'].config(bg=selection_bg)
                self.labels[title+'-box'].config(bg=selection_bg, relief='ridge', bd=5)
            def on_hover(event, papers=papers, paper=paper):
                self.hovering = papers[paper]
                if self.hovering != self.selection:
                    title = papers[paper]['title']
                    self.labels[title].config(bg=hover_color)
                    self.labels[title+'-authors'].config(bg=hover_color)
                    self.labels[title+'-pubinfo'].config(bg=hover_color)
                    self.labels[title+'-box'].config(bg=hover_color)
            hover_callbacks[title+'-enter'] = on_hover
            def on_leave(event, papers=papers, paper=paper):
                self.hovering = {}
                if papers[paper] != self.selection:
                    title= papers[paper]['title']
                    self.labels[title].config(bg=title_bg)
                    self.labels[title+'-authors'].config(bg=papers_bg)
                    self.labels[title+'-pubinfo'].config(bg=papers_bg)
                    self.labels[title+'-box'].config(bg=papers_bg)
            hover_callbacks[title+'-leave'] = on_leave
            self.labels[title].bind('<Enter>', hover_callbacks[title+'-enter'])
            self.labels[title+'-authors'].bind('<Enter>', hover_callbacks[title+'-enter'])
            self.labels[title+'-pubinfo'].bind('<Enter>', hover_callbacks[title+'-enter'])
            self.labels[title+'-box'].bind('<Enter>', hover_callbacks[title+'-enter'])
            self.labels[title].bind('<Leave>', hover_callbacks[title+'-leave'])
            self.labels[title+'-authors'].bind('<Leave>', hover_callbacks[title+'-leave'])
            self.labels[title+'-pubinfo'].bind('<Leave>', hover_callbacks[title+'-leave'])
            self.labels[title+'-box'].bind('<Leave>', hover_callbacks[title+'-leave'])


    def _select_paper(self, event):
        if self.hovering != {} and self.hovering != self.selection:
            if self.selection != {}:
                try:
                    past_sel = self.selection['title']
                    self.labels[past_sel].config(bg=title_bg)
                    self.labels[past_sel+'-authors'].config(bg=papers_bg)
                    self.labels[past_sel+'-pubinfo'].config(bg=papers_bg)
                    self.labels[past_sel+'-box'].config(bg=papers_bg, relief='flat', bd=0)
                except:
                    None
            self.selection = self.hovering
            title = self.selection['title']
            self.labels[title].config(bg=selection_bg)
            self.labels[title+'-authors'].config(bg=selection_bg)
            self.labels[title+'-pubinfo'].config(bg=selection_bg)
            self.labels[title+'-box'].config(bg=selection_bg, relief='ridge', bd=5)
            self.root.elements[Filters].selected_paper_title.set(self.selection['title'])
            self.root.elements[Filters].selected_paper_authors.set(self.selection['authors'])
            self.root.elements[Filters].selected_paper_pubinfo.set(self.selection['pubinfo'])
            self.root.elements[Filters].save_button.grid(row=self.root.elements[Filters].row, column=0,columnspan=3, padx=(85, 0), pady=(0, 100), sticky='w')
            
        elif self.hovering != {} and self.hovering == self.selection:
            title = self.selection['title']
            self.labels[title].config(bg=title_bg)
            self.labels[title+'-authors'].config(bg=hover_color)
            self.labels[title+'-pubinfo'].config(bg=hover_color)
            self.labels[title+'-box'].config(bg=hover_color, relief='flat', bd=0)
            self.selection = {}
            self.root.elements[Filters].save_button.grid_forget()
            self.root.elements[Filters].selected_paper_title.set('')
            self.root.elements[Filters].selected_paper_authors.set('')
            self.root.elements[Filters].selected_paper_pubinfo.set('')
            
        
    
    def _get_abstract(self, journal, paper):
        self.update_idletasks()
        if journal[paper]['abstract'] == '':
            link = journal[paper]['link']
            paper_page_html = url.urlopen(link)
            paper_page = BeautifulSoup(paper_page_html, 'lxml')
            
            if journal == self.prb_papers or journal == self.root.elements[Filters].prb_hits:
                abstract = paper_page.find_all('p')[0].text
            if journal == self.nat_papers or journal == self.root.elements[Filters].nat_hits:
                abstract = paper_page.find_all('p')[4].text
            if journal == self.arx_papers or journal == self.root.elements[Filters].arx_hits:
                abstract = paper_page.find_all('blockquote')[0].text.split('Abstract: ')[1]
            journal[paper]['abstract'] = abstract
        else:
            abstract = journal[paper]['abstract']
        
        abstract_window = tk.Tk()
        abstract_window.title('')
        aw_frame = tk.Frame(abstract_window, bg=abstract_bg)
        aw_frame.pack(side='top', fill='both', expand=True)
        
        title_label = tk.Label(aw_frame, text=paper, font=title_font, bg=abstract_bg, wraplength=900, justify='left')
        title_label.grid(row=0, column=0, padx=40, sticky='w')
        authors_label = tk.Label(aw_frame, text=journal[paper]['authors'], font=authors_font, bg=abstract_bg, wraplength=800, justify='left')
        authors_label.grid(row=1, column=0, padx=40, sticky='w')
        text = tk.Label(aw_frame, text=abstract, wraplength=800, bg=abstract_bg, justify='left')
        text.grid(row=2, column=0, sticky='w', padx=65, pady=40)
        
        

    def _on_configure(self, event):
        frame_height = self.frame.winfo_height()
        self.configure(height=frame_height)
        self.configure(scrollregion=self.bbox('all'))
        self.update_idletasks()
        frame_height = self.frame.winfo_height()
        self.configure(height=frame_height)
        self.configure(scrollregion=self.bbox('all'))
    
    
    def _scroll_papers(self, event):
        self.root.scroller = 'papers'

        
    def _on_mouse_wheel(self, event):
        if self.root.scroller == 'papers':
            self.yview_scroll(int(-1*(event.delta/120)), 'units')
        if self.root.scroller == 'db_handler':
            self.root.elements[Filters].db_handler.yview_scroll(int(-1*(event.delta/120)), 'units')

        

        

class Filters(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root, bg=filters_bg)
        self.root = root
        self._searched = False
        root.bind('<Return>', self._search)
        self.prb_hits = {}
        self.nat_hits = {}
        self.arx_hits = {}
        
        row = 0
        self.search_str = tk.StringVar()
        search_box = tk.Entry(self, textvariable=self.search_str, width=45)
        search_box.grid(row=row, column=0, padx=3, pady=20, sticky='w')
        search_button = tk.Button(self, text='Search', command=self._search)
        search_button.grid(row=row, column=1, columnspan=3, sticky='w')
        
        row += 1
        self.num_results = tk.StringVar()
        self._count_results()
        results_label = tk.Label(self, textvariable=self.num_results, bg=filters_bg)
        results_label.grid(row=row, column=0)
        
        row += 1
        format_line = tk.Label(self, text='_'*115, bg=filters_bg)
        format_line.grid(row=row, column=0, columnspan=3, sticky='w')
        
        row += 1
        journal_filter_label = tk.Label(self, text='Journals', bg=filters_bg, font=filters_font)
        journal_filter_label.grid(row=row, column=0, padx=10, pady=15, sticky='e')
        
        row += 1
        self.prb_toggle = tk.IntVar(root, value=1)
        prb_toggle_button = tk.Checkbutton(self, text='Physical Review B', variable=self.prb_toggle, font=filters_list_font, bg=filters_bg)
        prb_toggle_button.grid(row=row, column=0, padx=(100, 0), sticky='w')
        
        new_journal_toggle_button = tk.Checkbutton(self, text='Another Journal', font=filters_list_font, bg=filters_bg)
        new_journal_toggle_button.grid(row=row, column=1, padx=(10, 250), sticky='w')
        
        row += 1
        self.nat_toggle = tk.IntVar(root, value=1)
        nat_toggle_button = tk.Checkbutton(self, text='Nature', variable=self.nat_toggle, font=filters_list_font, bg=filters_bg)
        nat_toggle_button.grid(row=row, column=0, padx=(100, 0), sticky='w')

        new_journal_toggle_button = tk.Checkbutton(self, text='Another Journal', font=filters_list_font, bg=filters_bg)
        new_journal_toggle_button.grid(row=row, column=1, padx=(10, 250), sticky='w')
        
        row += 1
        self.arx_toggle = tk.IntVar(root, value=1)
        arx_toggle_button = tk.Checkbutton(self, text='arXiv', variable=self.arx_toggle, font=filters_list_font, bg=filters_bg)
        arx_toggle_button.grid(row=row, column=0, padx=(100, 0), sticky='w')

        new_journal_toggle_button = tk.Checkbutton(self, text='Another Journal', font=filters_list_font, bg=filters_bg)
        new_journal_toggle_button.grid(row=row, column=1, padx=(10, 250), sticky='w')

        row += 1
        format_line = tk.Label(self, text='_'*115, bg=filters_bg)
        format_line.grid(row=row, column=0, columnspan=3, sticky='w')
        
        row += 1
        self.selected_paper_title = tk.StringVar(root, '')
        selected_paper_title_label = tk.Label(self, textvariable=self.selected_paper_title, font=title_font, bg=filters_bg, wraplength=850, justify='left')
        selected_paper_title_label.grid(row=row, column=0, columnspan=2, padx=(25, 0), pady=(45, 0), sticky='w')
        row += 1
        self.selected_paper_authors = tk.StringVar(root, '')
        selected_paper_authors_label = tk.Label(self, textvariable=self.selected_paper_authors, font=authors_font, bg=filters_bg, wraplength=800, justify='left')
        selected_paper_authors_label.grid(row=row, column=0, columnspan=3, padx=(85, 0), pady=(15, 0), sticky='w')
        row += 1
        self.selected_paper_pubinfo = tk.StringVar(root, '')
        selected_paper_pubinfo_label = tk.Label(self, textvariable=self.selected_paper_pubinfo, font=authors_font, bg=filters_bg, wraplength=800, justify='left')
        selected_paper_pubinfo_label.grid(row=row, column=0,columnspan=3, padx=(85, 0), sticky='w')
        row += 1
        self.row = row
        self.save_button = tk.Button(self, text='Save this paper', command=self._save, font=authors_font, bg=button_color)
        row += 1
        
        self.db_handler = Database_Handler(self, self.root)
        self.db_handler.place(relx=0.0, rely=0.65, relwidth=1.0, relheight=0.34)
        
        
        
    def _search(self, event=1):
        self._searched = True
        search_str = self.search_str.get().lower()

        self.prb_hits = {}
        for key in self.root.elements[Papers].prb_papers.keys():
            paper = self.root.elements[Papers].prb_papers[key]
            if search_str in paper['title'].lower() or search_str in paper['abstract']:
                self.prb_hits[paper['title']] = paper
        
        self.nat_hits = {}
        for key in self.root.elements[Papers].nat_papers.keys():
            paper = self.root.elements[Papers].nat_papers[key]
            if search_str in paper['title'].lower() or search_str in paper['abstract']:
                self.nat_hits[paper['title']] = paper
    
        self.arx_hits = {}
        for key in self.root.elements[Papers].arx_papers.keys():
            paper = self.root.elements[Papers].arx_papers[key]
            if search_str in paper['title'].lower() or search_str in paper['abstract']:
                self.arx_hits[paper['title']] = paper   
        
        for key in self.root.elements[Papers].labels.keys():
            self.root.elements[Papers].labels[key].destroy()

        self.root.elements[Papers].row = 0
        if len(self.prb_hits) > 0 and self.prb_toggle.get() == 1:
            self.root.elements[Papers].show_papers(self.prb_hits)
        else:
            self.root.elements[Papers].prb_papers_label.grid_forget()
        if len(self.nat_hits) > 0 and self.nat_toggle.get() == 1:
            self.root.elements[Papers].show_papers(self.nat_hits)
        else:
            self.root.elements[Papers].nat_papers_label.grid_forget()
        if len(self.arx_hits) > 0 and self.arx_toggle.get() == 1:
            self.root.elements[Papers].show_papers(self.arx_hits)
        else:
            self.root.elements[Papers].arx_papers_label.grid_forget()

        self.root.elements[Papers]._on_configure(1)
        self._count_results()
    
    
    def _count_results(self):
        if self._searched:
            num = len(self.prb_hits)*self.prb_toggle.get() + len(self.nat_hits)*self.nat_toggle.get() + len(self.arx_hits)*self.arx_toggle.get()
        else:
            num = 'Search to filter'
        self.num_results.set(f'{num} results')
        
    
    def _save(self):
        with open(database_path, 'a', newline='') as db:
            w = csv.writer(db, dialect='excel')
            paper = self.root.elements[Papers].selection
            row = []
            for key in paper.keys():
                row.append(paper[key].encode('utf-8'))
            w.writerow(row)
            db.close()
        
        self.db_handler.saved_papers[row[0]] = {
                'title':row[0],
                'authors':row[1],
                'link':row[2],
                'pubinfo':row[3],
                'abstract':row[4]
                }
        
        for key in self.db_handler.labels.keys():
            self.db_handler.labels[key].destroy()
        self.db_handler.labels = {}
        self.db_handler.load_saved_papers()
        self.db_handler.show_saved_papers(self.db_handler.saved_papers)
        self.db_handler._on_configure(1)
            
    
    


            
class Database_Handler(tk.Canvas):
    def __init__(self, parent, root):
        tk.Canvas.__init__(self, parent, bg=papers_bg, relief='ridge', bd=5)
        self.root = root
        self.row = 0
        self.labels = {}
        self.selection = {}
        self.hovering = {}
        self.scrollbar = tk.Scrollbar(self, command=self.yview)
        self.scrollbar.pack(side='left', fill='y')
        self.configure(yscrollcommand = self.scrollbar.set)
        self.bind('<Configure>', self._on_configure)
        self.frame = tk.Frame(self, bg=papers_bg)
        self.create_window((0,0), window=self.frame, anchor='nw')
        self.bind('<Enter>', self._scroll_db_handler)
        
        self.load_saved_papers()
        self.show_saved_papers(self.saved_papers)
        self.scrollbar.tkraise()
        
        
    def load_saved_papers(self):
        self.saved_papers = {}
        with open(database_path, 'r') as db:
            rows = csv.reader(db, dialect='excel')
            for row in rows:
                row = [cell.split("b'", 1)[1][:len(cell.split("b'",1)[1])-1] for cell in row]
                self.saved_papers[row[0]] = {
                        'title':row[0],
                        'authors':row[1],
                        'link':row[2],
                        'pubinfo':row[3],
                        'abstract':row[4]
                        }
    
    def show_saved_papers(self, papers):
        self.row += 1
        link_callbacks = {}
        hover_callbacks = {}
        remove_callbacks = {}
        for paper in papers.keys():
            title = papers[paper]['title']
            authors = papers[paper]['authors']
            link = papers[paper]['link']
            def link_callback(event, link=link):
                webbrowser.open_new(link)
            link_callbacks[title] = link_callback
            self.labels[title+'-box'] = tk.Label(self.frame, bg=papers_bg, width=200)
            self.labels[title+'-box'].grid(row=self.row, column=1, rowspan=3, columnspan=3, pady=(0, 5), sticky='nsew')
            self.labels[title] = tk.Label(self.frame, text=title, font=title_font, bg=title_bg, cursor='hand2', wraplength=850, justify='left')
            self.labels[title].bind('<Button-1>', link_callbacks[title])
            self.labels[title].grid(row=self.row, column=1, padx=40, pady=(5, 0), sticky='w')
            self.row += 1
            self.labels[title+'-authors'] = tk.Label(self.frame, text=authors, font=authors_font, bg=papers_bg, wraplength=800, justify='left', state='normal', activebackground='red4')
            self.labels[title+'-authors'].grid(row=self.row, column=1, padx=100, sticky='w')
            def remove_paper(papers=papers, paper=paper):
                title = papers[paper]['title']
                self.labels[title+'-box'].destroy()
                self.labels[title].destroy()
                self.labels[title+'-authors'].destroy()
                self.labels[title+'-remove'].destroy()
                self.saved_papers = {k:self.saved_papers[k] for k in self.saved_papers.keys() if k != title}
                self._remove_from_database(papers[paper])
                print('working')
            remove_callbacks[title] = remove_paper
            self.labels[title+'-remove'] = tk.Button(self.frame, text='Remove', font=authors_font, bg=button_color, command=remove_callbacks[title])
            self.labels[title+'-remove'].grid(row=self.row-1, column=1, padx=900, sticky='w')
            self.row += 1
            def on_hover(event, papers=papers, paper=paper):
                self.hovering = papers[paper]
                title = papers[paper]['title']
                self.labels[title].config(bg=hover_color)
                self.labels[title+'-authors'].config(bg=hover_color)
                self.labels[title+'-box'].config(bg=hover_color)
            hover_callbacks[title+'-enter'] = on_hover
            def on_leave(event, papers=papers, paper=paper):
                self.hovering = {}
                title= papers[paper]['title']
                self.labels[title].config(bg=title_bg)
                self.labels[title+'-authors'].config(bg=papers_bg)
                self.labels[title+'-box'].config(bg=papers_bg)
            hover_callbacks[title+'-leave'] = on_leave
            self.labels[title].bind('<Enter>', hover_callbacks[title+'-enter'])
            self.labels[title+'-authors'].bind('<Enter>', hover_callbacks[title+'-enter'])
            self.labels[title+'-box'].bind('<Enter>', hover_callbacks[title+'-enter'])
            self.labels[title].bind('<Leave>', hover_callbacks[title+'-leave'])
            self.labels[title+'-authors'].bind('<Leave>', hover_callbacks[title+'-leave'])
            self.labels[title+'-box'].bind('<Leave>', hover_callbacks[title+'-leave'])
    
    
    def _remove_from_database(self, paper):
        with open(database_path, 'w+', newline='') as db:
            w = csv.writer(db, dialect='excel')
            for key in self.saved_papers.keys():
                pap = self.saved_papers[key]
                if pap == paper:
                    pass
                else:
                    row = []
                    for key in paper.keys():
                        row.append(pap[key].encode('utf-8'))
                    w.writerow(row)
        
        

    def _on_configure(self, event):
        frame_height = self.frame.winfo_height()
        self.configure(height=frame_height)
        self.configure(scrollregion=self.bbox('all'))
        self.update_idletasks()
        frame_height = self.frame.winfo_height()
        self.configure(height=frame_height)
        self.configure(scrollregion=self.bbox('all'))
        self.scrollbar.tkraise()
    
    
    def _scroll_db_handler(self, event):
        self.root.scroller = 'db_handler'    
    


    
if __name__ == '__main__':
    app = Main()
    app.mainloop()
        
        
