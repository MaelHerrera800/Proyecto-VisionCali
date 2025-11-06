import tkinter as tk
from tkinter import messagebox
import pyrebase

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

def ventana_usuario():
    user_win = tk.Toplevel()
    user_win.title("Ventana de Usuario")
    user_win.geometry("300x200")
    tk.Label(user_win, text="aun no esta terminado profe", font=("Arial", 14)).pack(pady=30)
    tk.Button(user_win, text="Cerrar", command=user_win.destroy).pack(pady=10)

def ventana_admin():
    admin_win = tk.Toplevel()
    admin_win.title("Panel de Administrador")
    admin_win.geometry("300x200")
    tk.Label(admin_win, text="Bienvenido Administrador", font=("Arial", 14)).pack(pady=30)
    tk.Button(admin_win, text="Cerrar", command=admin_win.destroy).pack(pady=10)

def ventana_operario():
    oper_win = tk.Toplevel()
    oper_win.title("Panel de Operario")
    oper_win.geometry("300x200")
    tk.Label(oper_win, text="Bienvenido Operario", font=("Arial", 14)).pack(pady=30)
    tk.Button(oper_win, text="Cerrar", command=oper_win.destroy).pack(pady=10)


# --- FUNCIONES DE LOGIN ---

def login_admin():
    def iniciar():
        email = entry_email.get()
        password = entry_password.get()
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            messagebox.showinfo("Éxito", f"Bienvenido Administrador: {email}")
            login_win.destroy()
            ventana_admin()
        except Exception as e:
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
        except Exception as e:
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


# --- VENTANA PRINCIPAL ---
ventana = tk.Tk()
ventana.title("MENÚ DE VISIÓNCALI")
ventana.geometry("300x250")
ventana.config(bg="#f0f0f0")

tk.Label(ventana, text="Seleccione su rol", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=10)

tk.Button(ventana, text="Administrador", command=login_admin, bg="#4CAF50", fg="white", width=20).pack(pady=10)
tk.Button(ventana, text="Operario", command=login_operario, bg="#2196F3", fg="white", width=20).pack(pady=10)
tk.Button(ventana, text="Usuario", command=ventana_usuario, bg="#E21717", fg="white", width=20).pack(pady=10)

ventana.mainloop() 

if __name__ == "__main__":
    ventana.mainloop()