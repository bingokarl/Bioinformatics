# Bellfort Sequence Parser

## Modules

import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkf
from tkinter import messagebox
from tkinter import filedialog
import threading
import time

## Helper Functions
### Reverse Complement

def reverseComplement(sequence):
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
    rc_sequence=''
    for s in sequence:
        rc_sequence = complement[s] + rc_sequence
    return rc_sequence

### FASTQ File Browse

def buttonBrowseFASTQ():
    global filenameFASTQ
    
    try:
        filenameFASTQ = filedialog.askopenfilename(filetypes=(('FASTQ files', '*.fastq'), 
                                                              ('All files', '*.*')))
        text_fileFASTQ.delete('1.0', tk.END)
        text_fileFASTQ.insert('1.0', filenameFASTQ.split('/')[-1])
    except:
        filenameFASTQ = ''   

### FASTQ File Load

def loadFASTQ():
    global reads
    
    start_time = time.time()    
    
    f = open(filenameFASTQ)

    reads = []

    try:
        while 1:
            name = f.readline().rstrip()
            sequence = f.readline().rstrip()
            f.readline()
            quality = f.readline().rstrip()

            if len(name) == 0:
                break

            union = name, sequence

            reads.append(union)           

        end_time = time.time()
        delta_time = end_time - start_time

        text_time.delete('1.0', tk.END)
        text_time.insert('1.0', str(delta_time))  

        text_readNum.delete('1.0', tk.END)
        text_readNum.insert('1.0', str(len(reads)))  

    except:
        messagebox.showwarning("File Loading Failed", 
                               "Sorry, file loading failed! Please check the file format.")
    f.close()

def start_loadFASTQ_thread(event):
    global loadFASTQ_thread
    
    if filenameFASTQ != '':
        loadFASTQ_thread = threading.Thread(target=loadFASTQ)
        loadFASTQ_thread.daemon = True

        progressbar_loadFASTQ.start(10)
        loadFASTQ_thread.start()
        root.after(20, check_loadFASTQ_thread)
    else:
        messagebox.showwarning("No File", 
                               "Sorry, no file loaded! Please choose FASTQ file first.")

def check_loadFASTQ_thread():
    if loadFASTQ_thread.is_alive():
        progressbar_loadFASTQ.start(10)
        root.after(20, check_loadFASTQ_thread)
    else:
        progressbar_loadFASTQ.stop()
        progressbar_loadFASTQ['value']=100
        messagebox.showinfo("FASTQ File Loaded", "FASTQ file successfully loaded!")

### Preprocess

def preprocessFASTQ():
    global reads, indicator_preprocess, kmer_dict_reads
    
    try:
        num = len(reads)   
        indicator_preprocess = 0
        gain = 500000/num

        gotten = text_sequence_len.get('1.0', tk.END)
        k = int(gotten.rstrip())
        
        if k > len(reads[0][1]):
            messagebox.showwarning("Target Sequence Length Error", 
                                   "Sorry, the target sequence length is more than read length. Please check.")
        elif k < 3:
            messagebox.showwarning("Sequence Too Short", 
                                   "Sorry, the target sequence length is too short which will make the program running slowly. Please check.")
        else:
            kmer_dict_reads = {}

            start_time = time.time()

            for read in reads:
                for i in range(len(read[1])-k+1):
                    kmer_dict_reads[read[1][i:i+k]] = set()
                indicator_preprocess += gain 

            for read in reads:
                for i in range(len(read[1])-k+1):
                    kmer_dict_reads[read[1][i:i+k]].add(read)
                indicator_preprocess += gain

            end_time = time.time()
            delta_time = end_time - start_time

            text_time.delete('1.0', tk.END)
            text_time.insert('1.0', str(delta_time))

            messagebox.showinfo("Preprocess FASTQ Completed", 
                                "Current FASTQ preprocess successfully completed!")

    except NameError:
        messagebox.showwarning("No FASTQ File Loaded", 
                               "Sorry, no loaded FASTQ file found! Please load FASTQ file first.")

def start_preprocess_thread(event):
    global preprocess_thread, indicator_preprocess
    preprocess_thread = threading.Thread(target=preprocessFASTQ)
    preprocess_thread.daemon = True
    
    progressbar['value'] = indicator_preprocess
    
    preprocess_thread.start()
    root.after(20, check_preprocess_thread)

def check_preprocess_thread():
    if preprocess_thread.is_alive():
        progressbar['value'] = indicator_preprocess
        
        root.after(20, check_preprocess_thread)

### Match All

def matchAll():
    global  kmer_dict_reads, indicator_matchAll, df
    
    try:
        len(kmer_dict_reads)    
        num = len(df)
        
        if num == 0:
            messagebox.showwarning("No Sequences Loaded", 
                                   "Sorry, no sequences loaded! Please load sequences first.")
        else:    
            indicator_matchAll = 0
            gain = 1000000/num

            start_time = time.time()

            arr = np.array(df)

            for i in range(len(arr)):
                key1 = arr[i,2]
                key2 = reverseComplement(key1)
                
                try:
                    n1 = len(kmer_dict_reads[key1])
                except KeyError:
                    n1 = 0
                    
                try:
                    n2 = len(kmer_dict_reads[key2])
                except KeyError:
                    n2 = 0
                    
                arr[i, 4] = n1 + n2
                arr[i, 5] = 'Checked'
                
                indicator_matchAll += gain

            df = pd.DataFrame(arr, columns = ['gene_id', 'UID', 'seq', 'Reserved', 'Count', 'Tag'])
            #df = df.set_index('UID', drop=False) 

            end_time = time.time()
            delta_time = end_time - start_time

            text_time.delete('1.0', tk.END)
            text_time.insert('1.0', str(delta_time))

            messagebox.showinfo("Matching Completed", 
                                "Counting of sequences matched successfully completed!")

    except NameError:
        messagebox.showwarning("No FASTQ Preprocessed or No Sequences Loaded", 
                               "Sorry, no FASTQ preprocess implemented or no sequences file loaded! Please preprocess FASTQ or load sequences first.")    

def start_matchAll_thread(event):
    global matchAll_thread, indicator_matchAll
    matchAll_thread = threading.Thread(target=matchAll)
    matchAll_thread.daemon = True
    
    progressbar['value'] = indicator_matchAll
    
    matchAll_thread.start()
    root.after(20, check_matchAll_thread)

def check_matchAll_thread():
    if matchAll_thread.is_alive():
        progressbar['value'] = indicator_matchAll
        
        root.after(20, check_matchAll_thread)

### Match Single

def buttonMatch():
    gotten = text_sequence.get('1.0', tk.END)
    p1 = gotten.rstrip()    
    p2 = reverseComplement(p1)
    
    if p1 == '' or p2 == '':
        messagebox.showwarning("No Sequence Found", 
                               "Sorry, no sequence found in the text blank above! Please check the sequence.")
    else:
        try:
            len(kmer_dict_reads)
            try:
                n1 = len(kmer_dict_reads[p1])
            except KeyError:
                n1 = 0
            
            try:
                n2 = len(kmer_dict_reads[p2])
            except KeyError:
                n2 = 0
                
            count = n1 + n2
                
            text_count.delete('1.0', tk.END)
            text_count.insert('1.0', str(count))
            
        except NameError:
            messagebox.showwarning("No FASTQ Preprocessed", 
                                   "Sorry, no FASTQ preprocess implemented! Please preprocess FASTQ first.")

### File of Target Sequence Load

def buttonBrowseSequences():
    global filenameSequences
    progressbar_loadSequences['value'] = 0
    try:
        filenameSequences = filedialog.askopenfilename(filetypes=(('Comma-Separated (CSV) text file', '*.csv'), ('All files', '*.*')))
        text_fileSequences.delete('1.0', tk.END)
        text_fileSequences.insert('1.0', filenameSequences.split('/')[-1])
    except:
        filenameSequences = ''    

def loadSequences():
    global filenameSequences, df, recordNum
   
    if filenameSequences == '':
        messagebox.showwarning("No File", "Sorry, no file chosen! Please choose file of sequences first.")
    else:        
        try:
            start_time = time.time()
            
            df = pd.read_csv(filenameSequences)
            df['count'] = 0
            df['tag'] = ''
            #df = df.set_index('UID', drop=False)  
            
            recordNum = len(df)
            
            progressbar_loadSequences['value'] = 100
            
            end_time = time.time()
            delta_time = end_time - start_time
                       
            text_time.delete('1.0', tk.END)
            text_time.insert('1.0', str(delta_time))
            
            text_recordNum.delete('1.0', tk.END)
            text_recordNum.insert('1.0', str(recordNum))
            
            messagebox.showinfo("File of Sequences Loaded", "File of sequences successfully loaded!")        
        except:
            messagebox.showwarning("File Loading Failed", "Sorry, file loading failed! Please check the file format.")    

### Table Events

def OnDoubleClick(event):
    item = table.selection()[0]
    value = table.item(item, 'values')
    geneID = value[0]
    uid = value[1]
    sequence = value[2]
    rc_sequence = reverseComplement(sequence)
    
    text_geneID.delete('1.0', tk.END)
    text_geneID.insert('1.0', str(geneID))
    
    text_uid.delete('1.0', tk.END)
    text_uid.insert('1.0', str(uid))
    
    text_sequence.delete('1.0', tk.END)
    text_sequence.insert('1.0', str(sequence))
    
    text_rc_sequence.delete('1.0', tk.END)
    text_rc_sequence.insert('1.0', str(rc_sequence))
    

def sortby(tree, col, descending):
    """sort tree contents when a column header is clicked on"""
    # grab values to sort
    data = [(tree.set(child, col), child) for child in tree.get_children('')]
    # if the data to be sorted is numeric change to float
    #data =  change_numeric(data)
    # now sort the data in place
    data.sort(reverse=descending)
    for ix, item in enumerate(data):
        tree.move(item[1], '', ix)
    # switch the heading so it will sort in the opposite direction
    tree.heading(col, command=lambda col=col: sortby(tree, col, int(not descending)))

def display_in_table():
    try:
        for a in df.index:
            row = df.ix[a]
            table.insert("", "end", "", values=tuple(row)) 
    except NameError:
        messagebox.showwarning("No Sequences to be Displayed", 
                               "Sorry, there's no loaded sequences to be displayed! Please load sequence file first.") 

### Other Button Functions

def clear():
    for i in table.get_children():
        table.delete(i)

def browse():
    start_time = time.time()
    clear()
    display_in_table()
    delta_time = time.time() - start_time
    
    text_time.delete('1.0', tk.END)
    text_time.insert('1.0', str(delta_time))           

def buttonExport():   
    if filenameSequences == '' or filenameFASTQ == '':
        messagebox.showwarning("No File Loaded", 
                               "Sorry, no file loaded! Please choose sequence file and FASTQ file first.")
    else:
        try:
            len(df)
            len(reads)
            directory = filedialog.askdirectory()
            df.to_csv(directory + '/' +'SequenceCounts.csv')
            messagebox.showinfo("File Exported", "File of counted sequences successfully exported!")        
        except NameError:
            messagebox.showwarning("Error: No Counted DataFrame Generated", 
                               "Sorry, no effective counted DataFrame generated! Please check the previous workflow.")

def buttonAbout():
    about_root=tk.Tk()
    
    w = 367 # width for the Tk root
    h = 310 # height for the Tk root

    # get screen width and height
    ws = about_root.winfo_screenwidth() # width of the screen
    hs = about_root.winfo_screenheight() # height of the screen

    # calculate x and y coordinates for the Tk root window
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)

    # set the dimensions of the screen 
    # and where it is placed
    about_root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    about_root.title('About Bellfort Sequence Parser')  
    about_root.iconbitmap('dna.ico')

    label_author=tk.Label(about_root,text='Bellfort Sequence Parser Version 1.0', font=('tahoma', 9))
    label_author.place(x=90,y=30)

    label_author=tk.Label(about_root,text='Copyright (C) 2016', font=('tahoma', 9))
    label_author.place(x=125,y=60)
    
    label_author=tk.Label(about_root,text='Chen Lab', font=('tahoma', 9))
    label_author.place(x=150,y=90)
    
    label_author=tk.Label(about_root,text='Human Genome Sequencing Center', font=('tahoma', 9))
    label_author.place(x=80,y=120)
    
    label_author=tk.Label(about_root,text='Department of Molecular and Human Genetics', font=('tahoma', 9))
    label_author.place(x=50,y=150)
    
    label_author=tk.Label(about_root,text='Baylor College of Medicine', font=('tahoma', 9))
    label_author.place(x=110,y=180)
   

    button_okay=ttk.Button(about_root, width=15, text='OK', command=about_root.destroy)
    button_okay.place(x=130, y=235)

    about_root.mainloop()

## Main Flow

headers = ['gene_id', 'UID', 'seq', 'Reserved', 'count', 'tag']
header_widths = [280, 150, 350, 100, 80, 100]

root = tk.Tk()

indicator_preprocess = 0
indicator_loadSequences = 0
indicator_matchAll = 0
filenameSequences = ''
filenameFASTQ = ''
recordNum = 0
count = 0

root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
#root.attributes('-fullscreen', True)
root.title('Bellfort Sequence Parser')
root.iconbitmap('dna.ico')


# Multicolumn Listbox/////////////////////////////////////////////////////////////////////////////
table = ttk.Treeview(height="20", columns=headers, selectmode="extended")
table.pack(padx=10, pady=20, ipadx=1200, ipady=130)

i = 1
for header in headers:
    table.heading('#'+str(i), text=header.title(), anchor=tk.W, command=lambda c=header: sortby(table, c, 0))
    table.column('#'+str(i), stretch=tk.NO, minwidth=0, width=tkf.Font().measure(header.title())+header_widths[i-1]) 
    i+=1    
table.column('#0', stretch=tk.NO, minwidth=0, width=0)

table.bind("<Double-1>", OnDoubleClick)
#///////////////////////////////////////////////////////////////////////////////////////////

# Scrollbar////////////////////////////////////////////////////////////////////////////////////////
vsb = ttk.Scrollbar(table, orient="vertical",  command = table.yview)
hsb = ttk.Scrollbar(table, orient="horizontal", command = table.xview)
## Link scrollbars activation to top-level object
table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
## Link scrollbar also to every columns
map(lambda col: col.configure(yscrollcommand=vsb.set,xscrollcommand=hsb.set), table)
vsb.pack(side = tk.RIGHT, fill = tk.Y)
hsb.pack(side = tk.BOTTOM, fill = tk.X)        

#//////////////////////////////////////////////////////////////////////////////////////////////
y0 =370
y1 = 410
y2 = 480
y3 = 520
y4 = 580
y5 = 615
y6 = 655
y7 = 695
# Text /////////////////////////////////////////////////////////////////////////////////////
text_recordNum=tk.Text(root, width=18, height=1, font=('tahoma', 9), bd=2, wrap='none')
text_recordNum.place(x=830, y=y0)
label_recordNum=tk.Label(root, text='records', font=('tahoma', 9))
label_recordNum.place(x=1000,y=y0)

text_fileSequences=tk.Text(root, width=50, height=1, font=('tahoma', 9), bd=2, wrap='none')
text_fileSequences.place(x=60, y=y0)

text_fileFASTQ=tk.Text(root, width=36, height=1, font=('tahoma', 9), bd=2, wrap='none')
text_fileFASTQ.place(x=60, y=y4)

text_count=tk.Text(root, width=16, height=1, font=('tahoma', 9), bd=2)
text_count.place(x=1000, y=y3)
label_count=tk.Label(root, text='Count:', font=('tahoma', 9))
label_count.place(x=940,y=y3)

text_geneID=tk.Text(root, width=20, height=1, font=('tahoma', 9), bd=2)
text_geneID.place(x=140, y=y2)
label_geneID=tk.Label(root, text='Gene ID:', font=('tahoma', 9))
label_geneID.place(x=60,y=y2)

text_uid=tk.Text(root, width=20, height=1, font=('tahoma', 9), bd=2)
text_uid.place(x=390, y=y2)
label_uid=tk.Label(root, text='UID:', font=('tahoma', 9))
label_uid.place(x=340,y=y2)

text_sequence=tk.Text(root, width=38, height=1, font=('tahoma', 9), bd=2)
text_sequence.place(x=680, y=y2)
label_sequence=tk.Label(root, text='Sequence:', font=('tahoma', 9))
label_sequence.place(x=600,y=y2)

text_rc_sequence=tk.Text(root, width=38, height=1, font=('tahoma', 9), bd=2)
text_rc_sequence.place(x=1000, y=y2)

text_sequence_len=tk.Text(root, width=10, height=1, font=('tahoma', 9), bd=2)
text_sequence_len.place(x=970, y=y5)
label_sequence_len=tk.Label(root, text='nts', font=('tahoma', 9))
label_sequence_len.place(x=1070,y=y5)
text_sequence_len.delete('1.0', tk.END)
text_sequence_len.insert('1.0', str(20))

text_readNum=tk.Text(root, width=22, height=1, font=('tahoma', 9), bd=2, wrap='none')
text_readNum.place(x=400, y=y6)
label_readNum=tk.Label(root, text='reads', font=('tahoma', 9))
label_readNum.place(x=600,y=y6)

text_time=tk.Text(root, width=15, height=1, font=('tahoma', 9), bd=2)
text_time.place(x=115, y=y7)
label_time=tk.Label(root, text='Time:', font=('tahoma', 9))
label_time.place(x=60,y=y7)
label_seconds=tk.Label(root, text='second(s)', font=('tahoma', 9))
label_seconds.place(x=260,y=y7)

# ProgressBar /////////////////////////////////////////////////////////////////////////////
progressbar_loadSequences = ttk.Progressbar(root, length=200, maximum=100, mode='determinate')
progressbar_loadSequences.place(x=500,y=y0)

progressbar_loadFASTQ = ttk.Progressbar(root, length=250, mode='indeterminate')
progressbar_loadFASTQ.place(x=400,y=y4)

progressbar = ttk.Progressbar(root, length=410, maximum=1000000, mode='determinate')
progressbar.place(x=720,y=y4)

# Button /////////////////////////////////////////////////////////////////////////////////
button_browseSequences = ttk.Button(root, text="Browse sgRNA...", width=20, command=buttonBrowseSequences)
button_browseSequences.place(x=60, y=y1)

button_loadSequences = ttk.Button(root, text="Load sgRNA", width=20, command=loadSequences)
button_loadSequences.place(x=500, y=y1)

button_clear = ttk.Button(root, text="Clear", width=20, command=clear)
button_clear.place(x=1180, y=y1)

button_refresh = ttk.Button(root, text="Browse", width=20, command=browse)
button_refresh.place(x=1180, y=y0)

button_browseFASTQ = ttk.Button(root, text="Browse FASTQ...", width=20, command=buttonBrowseFASTQ)
button_browseFASTQ.place(x=60, y=y5)

button_loadFASTQ = ttk.Button(root, text="Load FASTQ", width=20, command=lambda:start_loadFASTQ_thread(None))
button_loadFASTQ.place(x=400, y=y5)

button_preprocessFASTQ = ttk.Button(root, text="Preprocess FASTQ", width=20, command=lambda:start_preprocess_thread(None))
button_preprocessFASTQ.place(x=720, y=y5)

button_match = ttk.Button(root, text="Match", width=20, command=buttonMatch)
button_match.place(x=680, y=y3)

button_matchAll = ttk.Button(root, text="Match All", width=20, command=lambda:start_matchAll_thread(None))
button_matchAll.place(x=1180, y=y5)

button_about = ttk.Button(root, text="About", width=20, command=buttonAbout)
button_about.place(x=980, y=y7)

button_export = ttk.Button(root, text="Export", width=20, command=buttonExport)
button_export.place(x=720, y=y7)

button_exit = ttk.Button(root, text="Exit", width=20, command=root.destroy)
button_exit.place(x=1180, y=y7)

root.bind('<Return>', start_preprocess_thread)
root.bind('<Return>', start_loadFASTQ_thread)
root.bind('<Return>', start_matchAll_thread)

root.mainloop()