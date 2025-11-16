import tkinter as tk
from tkinter import messagebox
import pyrebase
import subprocess
import sys
import os
from PIL import Image, ImageTk

# CONFIGURACIÓN DE FIREBASE
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

def abrir_mapa():
    try:
        subprocess.Popen([sys.executable, "mapaMIO.py"])
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el módulo de mapa:\n{e}")

def abrir_graficas():
    try:
        subprocess.Popen([sys.executable, "Graficas.py"])
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
# INICIALIZACIÓN DEL SISTEMA
# -----------------------------------------------------
def inicializar_sistema():
    
    if not os.path.exists("predicciones_mio.xlsx"):
        try:
            from modelo_predictivo import ModeloPredictivoMIO_sklearn
            modelo = ModeloPredictivoMIO_sklearn(usar_ultimo_mes=False, usar_random_forest=True)
            modelo.entrenar_modelo_ocupacion()
            modelo.entrenar_modelo_colapso()
            df_pred = modelo.predecir(incluir_futuro=True, dias_futuros=5)
            if df_pred is not None:
                modelo.guardar_predicciones()
                print("Archivo 'predicciones_mio.xlsx' generado exitosamente.")
            else:
                print("No se pudo generar el DataFrame de predicciones.")
        except Exception as e:
            print("Error generando predicciones:", e)

# -----------------------------------------------------
# MENÚ PRINCIPAL
# -----------------------------------------------------
if __name__ == "__main__":
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
