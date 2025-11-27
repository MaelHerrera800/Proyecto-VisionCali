import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import pyrebase
import subprocess
import sys
import os
from PIL import Image, ImageTk
from dotenv import load_dotenv

from limpieza_mio import generar_datos_limpios
from modelo_predictivo import generar_predicciones_desde_archivo
from Graficas import mostrar_interfaz_desde_archivo
from Graficas_solo_tablas import mostrar_tablas_desde_archivo


# CONFIGURACIÓN DE FIREBASE
load_dotenv()

firebaseConfig = {
    "apiKey": os.getenv("API_KEY"),
    "authDomain": os.getenv("AUTH_DOMAIN"),
    "projectId": os.getenv("PROJECT_ID"),
    "databaseURL": os.getenv("DATABASE_URL"),
    "storageBucket": os.getenv("STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("MESSAGING_SENDER_ID"),
    "appId": os.getenv("APP_ID"),
    "measurementId": os.getenv("MEASUREMENT_ID")
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# 
# FUNCIONES DE VENTANAS SECUNDARIAS
# 
def ventana_usuario():
    try:
        subprocess.Popen([sys.executable, "Graficas_solo_tablas.py"])
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el módulo de tablas:\n{e}")

def ventana_admin():
    admin_win = tk.Toplevel()
    admin_win.title("Panel de Administrador")
    admin_win.geometry("300x300")

    tk.Label(admin_win, text="Bienvenido Administrador", font=("Arial", 14)).pack(pady=10)
    tk.Button(admin_win, text="Generar reporte", command=abrir_reporte, bg="#4CAF50", fg="white").pack(pady=5)
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

# -----------------------------------------------------
# FUNCIONES DE ABRIR MÓDULOS
# -----------------------------------------------------
def abrir_reporte():
    try:
        subprocess.Popen([sys.executable, "Reportes_finales.py"])
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el módulo de reportes:\n{e}")

def abrir_graficas():
    """Abre la interfaz de gráficas (sin subprocess)."""
    mostrar_interfaz_desde_archivo()


def abrir_tablas():
    """Abre la interfaz de solo tablas."""
    mostrar_tablas_desde_archivo()

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
# INICIALIZACIÓN DEL SISTEMA
# -----------------------------------------------------
def inicializar_sistema():
    ruta_data = os.path.join(BASE_DIR, "data_limpia_mio.xlsx")
    if not os.path.exists(ruta_data):
        generar_datos_limpios()
    ruta_pred = os.path.join(BASE_DIR, "predicciones_mio.xlsx")
    if not os.path.exists(ruta_pred):
        generar_predicciones_desde_archivo()
def mostrar_pantalla_carga():
    splash = tk.Tk()
    splash.overrideredirect(True)  # Quita bordes
    splash.geometry("400x300")

    # Fondo blanco
    frame = tk.Frame(splash, bg="white")
    frame.pack(fill="both", expand=True)

    # Logo opcional
    try:
        img = Image.open("logovisioncali.jpg")
        img = img.resize((160, 160))
        splash_logo = ImageTk.PhotoImage(img)
        label_img = tk.Label(frame, image=splash_logo, bg="white")
        label_img.image = splash_logo
        label_img.pack(pady=10)
    except:
        tk.Label(frame, text="VISIÓNCALI", font=("Arial", 20, "bold"), bg="white").pack(pady=10)

    # Texto de carga
    tk.Label(frame, text="Cargando el sistema...", font=("Arial", 12), bg="white").pack(pady=10)

    # Barra de progreso
    progreso = ttk.Progressbar(frame, orient="horizontal", length=250, mode="indeterminate")
    progreso.pack(pady=15)
    progreso.start(10)  # velocidad

    # Mostrar  segundos
    splash.after(5000, splash.destroy)

    splash.mainloop()

# -----------------------------------------------------
# MENÚ PRINCIPAL
# -----------------------------------------------------
if __name__ == "__main__":
    mostrar_pantalla_carga() 
    inicializar_sistema()
    root = tk.Tk()
    root.title("MENÚ DE VISIÓNCALI")
    root.geometry("300x350")
    root.config(bg="#f0f0f0")

    try:
        img = Image.open("logovisioncali.jpg")
        img = img.resize((180, 180))
        logo = ImageTk.PhotoImage(img)
        tk.Label(root, image=logo, bg="#f0f0f0").pack(pady=10)
        root.logo = logo
    except Exception as e:
        print("No se pudo cargar el logo:", e)

    tk.Label(root, text="Seleccione su rol", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=10)
    tk.Button(root, text="Administrador", command=login_admin, bg="#4CAF50", fg="white", width=20).pack(pady=10)
    tk.Button(root, text="Operario", command=login_operario, bg="#2196F3", fg="white", width=20).pack(pady=10)
    tk.Button(root, text="Usuario", command=ventana_usuario, bg="#E21717", fg="white", width=20).pack(pady=10)
    tk.Button(root, text="Cerrar", command=root.destroy, bg="#E74C3C", fg="white", width=20).pack(pady=10)
    root.mainloop()
