import tkinter as tk
from tkinter import messagebox
import pyrebase
import subprocess
import sys
import Graficas
import Reportes_finales
import webbrowser

# -----------------------------------------------------
# CONFIGURACIÓN DE FIREBASE
# -----------------------------------------------------

firebaseConfig = {
    "apiKey": "AIzaSyALWtfuk7-Ti9S2L0uFzJOtj_kkt9SS-5Q",
    "authDomain": "menu-del-mio.firebaseapp.com",
    "projectId": "menu-del-mio",
    "databaseURL": "https://menu-del-mio-default-rtdb.firebaseio.com/",
    "storageBucket": "menu-del-mio.firebasestorage.app",
    "messagingSenderId": "930983688745",
    "appId": "1:930983688745:web:517fed39a792495104ba38",
    "measurementId": "G-07JH7Y4RMZ"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# -----------------------------------------------------
# FUNCIONES DE VENTANAS SECUNDARIAS
# -----------------------------------------------------

def ventana_usuario():
    try:
        Graficas.mostrar_solo_tabla_colapsos()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo mostrar las estaciones que colapsarán:\n{e}")

def ventana_admin():
    admin_win = tk.Toplevel()
    admin_win.title("Panel de Administrador")
    admin_win.geometry("300x300")

    tk.Label(admin_win, text="Bienvenido Administrador", font=("Arial", 14)).pack(pady=10)

    tk.Button(admin_win, text="Generar reporte", command=abrir_reporte, bg="#4CAF50", fg="white",).pack(pady=5)
    tk.Button(admin_win, text="Ver gráficas", command=abrir_graficas, bg="#9B59B6", fg="white").pack(pady=5)
    tk.Button(admin_win, text="Ver Mapa", command=abrir_mapa).pack(pady=5)
    tk.Button(admin_win, text="Ver estaciones que se van a colapsar", command=ventana_usuario).pack(pady=5)
    tk.Button(admin_win, text="Cerrar", command=admin_win.destroy, bg="#E74C3C", fg="white").pack(pady=10)

def ventana_operario():
    oper_win = tk.Toplevel()
    oper_win.title("Panel de Operario")
    oper_win.geometry("300x250")
    tk.Label(oper_win, text="Bienvenido Operario", font=("Arial", 14)).pack(pady=10)
    tk.Button(oper_win, text="Ver Mapa", command=abrir_mapa).pack(pady=5)
    tk.Button(oper_win, text="Ver estaciones que se van a colapsar", command=ventana_usuario).pack(pady=5)
    tk.Button(oper_win, text="Cerrar", command=oper_win.destroy, bg="#E74C3C", fg="white").pack(pady=10)

# FUNCIÓNes DE ABRIR MÓDULOS
def abrir_reporte():
    """
    Abre el módulo de reportes (Reportes_finales.py) en una ventana separada.
    """
    try:
        subprocess.Popen([sys.executable, "Reportes_finales.py"])
        messagebox.showinfo("Reporte creado", "Reporte generado correctamente.")# se ejecuta como proceso aparte
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el módulo de reportes:\n{e}")
def abrir_mapa():
    """
    Abre el mapa de predicciones (HTML) generado por mapaMIO.py.
    Si no existe, ejecuta el script para generarlo.
    """
    import os
    if not os.path.exists("mapa_predicciones_mio_mañana.html"):
        try:
            import subprocess, sys
            subprocess.run([sys.executable, "mapaMIO.py"], check=True)
            messagebox.showinfo("Mapa creado", "Mapa generado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el mapa:\n{e}")
            return

    webbrowser.open("mapa_predicciones_mio_mañana.html")
    

def abrir_graficas():
    """
    Abre el módulo de gráficas (Graficas.py) en una ventana separada.
    """
    try:
        subprocess.Popen([sys.executable, "Graficas.py"])  # se ejecuta como proceso aparte
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el módulo de gráficas:\n{e}")

# -----------------------------------------------------
# FUNCIONES DE LOGIN
# -----------------------------------------------------

def login_admin():
    def iniciar():
        email = entry_email.get()
        password = entry_password.get()
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            messagebox.showinfo("Éxito", f"Bienvenido Administrador: {email}")
            login_win.destroy()
            ventana_admin()
        except Exception:
            messagebox.showerror("Error", "Credenciales inválidas o usuario no existe.")
    
    login_win = tk.Toplevel()
    login_win.title("Login Administrador")
    login_win.geometry("300x200")

    tk.Label(login_win, text="Email:").pack()
    entry_email = tk.Entry(login_win)
    entry_email.pack()

    tk.Label(login_win, text="Contraseña:").pack()
    entry_password = tk.Entry(login_win, show="*")
    entry_password.pack()

    tk.Button(login_win, text="Iniciar Sesión", command=iniciar, bg="#4CAF50", fg="white").pack(pady=10)

def login_operario():
    def iniciar():
        email = entry_email.get()
        password = entry_password.get()
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            messagebox.showinfo("Éxito", f"Bienvenido Operario: {email}")
            login_win.destroy()
            ventana_operario()
        except Exception:
            messagebox.showerror("Error", "Credenciales inválidas o usuario no existe.")
    
    login_win = tk.Toplevel()
    login_win.title("Login Operario")
    login_win.geometry("300x200")

    tk.Label(login_win, text="Email:").pack()
    entry_email = tk.Entry(login_win)
    entry_email.pack()

    tk.Label(login_win, text="Contraseña:").pack()
    entry_password = tk.Entry(login_win, show="*")
    entry_password.pack()

    tk.Button(login_win, text="Iniciar Sesión", command=iniciar, bg="#2196F3", fg="white").pack(pady=10)

# -----------------------------------------------------
# VENTANA PRINCIPAL
# -----------------------------------------------------

ventana = tk.Tk()
ventana.title("MENÚ DE VISIÓNCALI")
ventana.geometry("300x350")
ventana.config(bg="#f0f0f0")

tk.Label(ventana, text="Seleccione su rol", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=10)

tk.Button(ventana, text="Administrador", command=login_admin, bg="#4CAF50", fg="white", width=20).pack(pady=10)
tk.Button(ventana, text="Operario", command=login_operario, bg="#2196F3", fg="white", width=20).pack(pady=10)
tk.Button(ventana, text="Usuario", command=ventana_usuario, bg="#E21717", fg="white", width=20).pack(pady=10)


tk.Button(ventana, text="Cerrar", command=ventana.destroy, bg="#E74C3C", fg="white", width=20).pack(pady=10)

ventana.mainloop()

if __name__ == "__main__":
    ventana.mainloop()
