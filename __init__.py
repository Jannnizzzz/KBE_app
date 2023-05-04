import matlab.engine
MATLAB_ENG = matlab.engine.start_matlab()

def generate_warning(warning_header, msg):
    from tkinter import Tk, mainloop, X, messagebox
    # initialization
    window = Tk()
    window.withdraw()
    # generates message box
    messagebox.showwarning(warning_header, msg)