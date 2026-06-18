import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import os
import uuid
import zipfile
from io import BytesIO
from supabase import create_client

try:
    import google.generativeai as genai
except Exception:
    genai = None


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="LIFE OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "LIFE OS"
BASE_DATA_DIR = "data"
os.makedirs(BASE_DATA_DIR, exist_ok=True)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

COLUMNAS = {
    "tareas": [
        "id",
        "fecha",
        "tarea",
        "categoria",
        "prioridad",
        "repeticion",
        "completada",
    ],
    "finanzas": ["id", "fecha", "tipo", "categoria", "descripcion", "cantidad"],
    "wishlist": ["id", "nombre", "precio", "prioridad", "estado", "url"],
    "objetivos": ["id", "objetivo", "categoria", "progreso", "fecha_limite", "estado"],
    "proyectos": ["id", "proyecto", "tarea", "estado", "prioridad"],
    "notas": ["id", "fecha", "titulo", "nota", "categoria", "vinculo"],
    "calendario": ["id", "fecha", "hora", "titulo", "categoria", "notas"],
    "habitos": ["id", "habito", "categoria", "frecuencia"],
    "habitos_log": ["id", "fecha", "habito_id", "completado"],
    "compras": ["id", "item", "categoria", "cantidad", "comprado"],
    "suscripciones": ["id", "nombre", "categoria", "coste", "dia_cobro", "estado"],
    "universidad": [
        "id",
        "asignatura",
        "tipo",
        "descripcion",
        "fecha",
        "estado",
        "prioridad",
    ],
    "viajes": ["id", "viaje", "tipo", "descripcion", "fecha", "coste", "estado"],
    "presupuestos": ["id", "categoria", "limite_mensual"],
    "archivos": ["id", "fecha", "nombre", "categoria", "vinculo", "ruta"],
    "config": ["id", "clave", "valor"],
}

DATE_COLS = ["fecha", "fecha_limite"]
NUM_COLS = ["cantidad", "precio", "coste", "progreso", "limite_mensual", "dia_cobro"]
BOOL_COLS = ["completada", "comprado", "completado"]


# ============================================================
# STYLE
# ============================================================


def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 0%, rgba(59, 130, 246, 0.22), transparent 32%),
                radial-gradient(circle at 92% 5%, rgba(168, 85, 247, 0.18), transparent 28%),
                radial-gradient(circle at 55% 95%, rgba(20, 184, 166, 0.12), transparent 24%),
                #070a12;
            color: #ecfdf5;
        }

        header, footer, #MainMenu {
            visibility: hidden;
        }

        .block-container {
            max-width: 1500px;
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }

        section[data-testid="stSidebar"] {
            background: rgba(8, 13, 25, 0.86);
            backdrop-filter: blur(22px);
            border-right: 1px solid rgba(148, 163, 184, 0.16);
        }

        section[data-testid="stSidebar"] * {
            color: #e5e7eb !important;
        }

        h1, h2, h3 {
            letter-spacing: -0.045em;
            color: #f8fafc !important;
        }

        .hero {
            padding: 30px 32px;
            border-radius: 34px;
            border: 1px solid rgba(148, 163, 184, .20);
            background:
                linear-gradient(135deg, rgba(37, 99, 235, .25), rgba(124, 58, 237, .18)),
                rgba(15, 23, 42, .62);
            box-shadow: 0 30px 90px rgba(0,0,0,.32);
            margin-bottom: 22px;
        }

        .hero-title {
            font-size: 3.2rem;
            line-height: 1.02;
            font-weight: 900;
            color: #ffffff;
            margin: 0;
        }

        .hero-subtitle {
            color: #cbd5e1;
            font-size: 1.06rem;
            margin-top: 10px;
            max-width: 800px;
        }

        .glass {
            padding: 22px;
            border-radius: 26px;
            background: rgba(15, 23, 42, .70);
            border: 1px solid rgba(148, 163, 184, .18);
            box-shadow: 0 18px 60px rgba(0,0,0,.26);
            margin-bottom: 18px;
        }

        .mini-card {
            padding: 18px 18px;
            border-radius: 24px;
            background: linear-gradient(145deg, rgba(30,41,59,.90), rgba(15,23,42,.74));
            border: 1px solid rgba(148,163,184,.18);
            box-shadow: 0 18px 48px rgba(0,0,0,.22);
            min-height: 120px;
        }

        .mini-label {
            font-size: .84rem;
            color: #93c5fd;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .mini-value {
            font-size: 2rem;
            color: #f8fafc;
            font-weight: 900;
            letter-spacing: -.04em;
        }

        .mini-caption {
            color: #94a3b8;
            font-size: .86rem;
            margin-top: 5px;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 12px;
            border-radius: 999px;
            font-weight: 800;
            font-size: .82rem;
            margin: 3px 5px 3px 0;
            color: #dbeafe;
            background: rgba(37, 99, 235, .18);
            border: 1px solid rgba(96, 165, 250, .30);
        }

        .section-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 18px 20px;
            margin: 10px 0 18px 0;
            border-radius: 24px;
            border: 1px solid rgba(148, 163, 184, .16);
            background: rgba(15,23,42,.62);
        }

        .section-head-title {
            font-size: 1.55rem;
            font-weight: 900;
            color: #f8fafc;
            margin: 0;
        }

        .section-head-sub {
            color: #94a3b8;
            margin-top: 4px;
            font-size: .95rem;
        }

        .task-row {
            padding: 15px 16px;
            border-radius: 20px;
            background: rgba(15, 23, 42, .62);
            border: 1px solid rgba(148, 163, 184, .14);
            margin-bottom: 10px;
        }

        .alert {
            padding: 14px 16px;
            border-radius: 20px;
            background: rgba(15, 23, 42, .75);
            border: 1px solid rgba(148, 163, 184, .18);
            margin-bottom: 10px;
        }

        .alert strong {
            color: #f8fafc;
        }

        [data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(30, 41, 59, .92), rgba(15, 23, 42, .75));
            border: 1px solid rgba(148, 163, 184, .20);
            border-radius: 24px;
            padding: 18px;
            box-shadow: 0 18px 55px rgba(0,0,0,.26);
        }

        [data-testid="stMetricLabel"] p {
            color: #93c5fd !important;
            font-weight: 800;
        }

        [data-testid="stMetricValue"] {
            color: #f8fafc !important;
            font-weight: 900;
        }

        .stButton > button, .stDownloadButton > button {
            border-radius: 16px;
            border: 1px solid rgba(96, 165, 250, .36);
            background: linear-gradient(90deg, #2563eb, #7c3aed);
            color: white;
            font-weight: 800;
            box-shadow: 0 14px 34px rgba(37, 99, 235, .24);
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            filter: brightness(1.12);
            border-color: rgba(255,255,255,.58);
        }

        div[data-testid="stRadio"] label {
            background: rgba(15, 23, 42, .70);
            border: 1px solid rgba(148, 163, 184, .12);
            border-radius: 999px;
            padding: 6px 12px;
            margin-right: 4px;
        }

        div[data-testid="stExpander"] {
            background: rgba(15, 23, 42, .62);
            border: 1px solid rgba(148, 163, 184, .16);
            border-radius: 20px;
            overflow: hidden;
        }

        [data-testid="stDataFrame"] {
            border-radius: 22px;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, .15);
        }

        input, textarea {
            border-radius: 15px !important;
        }

        .sidebar-brand {
            padding: 18px 16px;
            border-radius: 26px;
            background:
                linear-gradient(135deg, rgba(37, 99, 235, .26), rgba(124, 58, 237, .18)),
                rgba(15,23,42,.78);
            border: 1px solid rgba(148, 163, 184, .18);
            margin-bottom: 14px;
        }

        .sidebar-brand-title {
            color: #ffffff;
            font-size: 1.65rem;
            font-weight: 950;
            letter-spacing: -.06em;
        }

        .sidebar-brand-sub {
            color: #cbd5e1;
            font-size: .9rem;
            margin-top: 3px;
        }

        .small-muted {
            color: #94a3b8;
            font-size: .9rem;
        }


        .top-nav-wrap {
            position: sticky;
            top: 0;
            z-index: 999;
            padding: 10px 0 16px 0;
            background: linear-gradient(180deg, rgba(7,10,18,.98), rgba(7,10,18,.70), rgba(7,10,18,0));
            backdrop-filter: blur(12px);
        }

        .nav-help {
            color: #94a3b8;
            font-size: .9rem;
            margin-bottom: 8px;
        }

        @media (max-width: 900px) {
            .hero-title {
                font-size: 2.3rem;
            }
            .hero {
                padding: 22px;
            }
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title, subtitle):
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
            <div style="margin-top:16px;">
                <span class="pill">☁️ Supabase</span>
                <span class="pill">🔐 Login</span>
                <span class="pill">📱 Mobile ready</span>
                <span class="pill">🤖 IA</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=""):
    st.markdown(
        f"""
        <div class="section-head">
            <div>
                <div class="section-head-title">{title}</div>
                <div class="section-head-sub">{subtitle}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_card(label, value, caption="", icon=""):
    st.markdown(
        f"""
        <div class="mini-card">
            <div class="mini-label">{icon} {label}</div>
            <div class="mini-value">{value}</div>
            <div class="mini-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


inject_css()


# ============================================================
# DATA HELPERS
# ============================================================


def new_id():
    return str(uuid.uuid4())


def slug(texto):
    texto = str(texto).strip().lower().replace(" ", "_")
    permitido = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    return "".join(c for c in texto if c in permitido) or "usuario"


def serializar_valor(v):
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    if isinstance(v, pd.Timestamp):
        return v.date().isoformat()
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def normalizar_df(df, nombre):
    cols = COLUMNAS[nombre]
    if df is None or df.empty:
        return pd.DataFrame(columns=cols)
    for c in cols:
        if c not in df.columns:
            df[c] = None
    for c in DATE_COLS:
        if c in df.columns and not df.empty:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    for c in NUM_COLS:
        if c in df.columns and not df.empty:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    for c in BOOL_COLS:
        if c in df.columns and not df.empty:
            df[c] = df[c].astype(str).str.lower().isin(["true", "1", "yes", "sí", "si"])
    return df[cols]


def backup_local(nombre, df):
    user_dir = os.path.join(BASE_DATA_DIR, usuario_actual)
    os.makedirs(user_dir, exist_ok=True)
    df.to_csv(os.path.join(user_dir, f"{nombre}.csv"), index=False)


def cargar_backup(nombre):
    path = os.path.join(BASE_DATA_DIR, usuario_actual, f"{nombre}.csv")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=COLUMNAS[nombre])
    return normalizar_df(pd.read_csv(path), nombre)


def cargar(nombre):
    try:
        res = (
            supabase.table("life_os_items")
            .select("id,data")
            .eq("user_id", usuario_actual)
            .eq("section", nombre)
            .execute()
        )
        filas = []
        for item in res.data or []:
            data = item.get("data") or {}
            data["id"] = item.get("id")
            filas.append(data)
        df = normalizar_df(pd.DataFrame(filas), nombre)
        backup_local(nombre, df)
        return df
    except Exception:
        st.sidebar.warning(f"Supabase no disponible en {nombre}. Usando copia local.")
        return cargar_backup(nombre)


def guardar(nombre, df):
    df = normalizar_df(df.copy(), nombre)
    try:
        (
            supabase.table("life_os_items")
            .delete()
            .eq("user_id", usuario_actual)
            .eq("section", nombre)
            .execute()
        )
        registros = []
        for _, row in df.iterrows():
            item_id = (
                str(row["id"])
                if pd.notna(row["id"]) and str(row["id"]).strip()
                else new_id()
            )
            data = {
                col: serializar_valor(row[col])
                for col in COLUMNAS[nombre]
                if col != "id"
            }
            registros.append(
                {
                    "id": item_id,
                    "user_id": usuario_actual,
                    "section": nombre,
                    "data": data,
                }
            )
        if registros:
            supabase.table("life_os_items").insert(registros).execute()
        backup_local(nombre, df)
    except Exception as e:
        st.error(f"Error guardando en Supabase ({nombre}): {e}")


def add(nombre, datos):
    datos = datos.copy()
    datos["id"] = new_id()
    df = cargar(nombre)
    guardar(nombre, pd.concat([df, pd.DataFrame([datos])], ignore_index=True))


def delete(nombre, item_id):
    try:
        supabase.table("life_os_items").delete().eq("id", item_id).eq(
            "user_id", usuario_actual
        ).eq("section", nombre).execute()
    except Exception as e:
        st.error(f"Error eliminando en Supabase: {e}")
    df = cargar(nombre)
    backup_local(nombre, df[df["id"] != item_id])


def update(nombre, item_id, cambios):
    df = cargar(nombre)
    for k, v in cambios.items():
        df.loc[df["id"] == item_id, k] = v
    guardar(nombre, df)


# ============================================================
# LOGIN
# ============================================================


def login_screen():
    hero(
        "LIFE OS",
        "Tu centro personal para organizar la vida, desde cualquier dispositivo.",
    )

    c1, c2, c3 = st.columns([1, 1.1, 1])
    with c2:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.subheader("Acceso")
        modo = st.radio("Modo", ["Iniciar sesión", "Crear cuenta"], horizontal=True)
        email = st.text_input("Email")
        password = st.text_input("Contraseña", type="password")

        if modo == "Iniciar sesión":
            if st.button("Entrar", use_container_width=True):
                if not email.strip() or not password.strip():
                    st.error("Introduce email y contraseña.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password(
                            {"email": email, "password": password}
                        )
                        st.session_state["auth_user_id"] = res.user.id
                        st.session_state["auth_email"] = res.user.email
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo iniciar sesión: {e}")
        else:
            st.caption("Si Supabase pide confirmar email, revisa tu correo.")
            if st.button("Crear cuenta", use_container_width=True):
                if not email.strip() or not password.strip():
                    st.error("Introduce email y contraseña.")
                elif len(password) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                else:
                    try:
                        supabase.auth.sign_up({"email": email, "password": password})
                        st.success("Cuenta creada. Ahora inicia sesión.")
                    except Exception as e:
                        st.error(f"No se pudo crear la cuenta: {e}")

        st.markdown("</div>", unsafe_allow_html=True)


if "auth_user_id" not in st.session_state:
    login_screen()
    st.stop()

usuario_actual = st.session_state["auth_user_id"]
usuario_email = st.session_state.get("auth_email", "usuario")

USER_DIR = os.path.join(BASE_DATA_DIR, slug(usuario_email))
FILES_DIR = os.path.join(USER_DIR, "archivos")
os.makedirs(FILES_DIR, exist_ok=True)


# ============================================================
# LOGIC
# ============================================================


def generar_repeticiones():
    tareas = cargar("tareas")
    if tareas.empty:
        return
    hoy = date.today()
    nuevas = []
    for _, r in tareas.iterrows():
        if r["repeticion"] == "No" or pd.isna(r["fecha"]) or r["fecha"] >= hoy:
            continue
        crear = (
            r["repeticion"] == "Diaria"
            or (r["repeticion"] == "Semanal" and r["fecha"].weekday() == hoy.weekday())
            or (r["repeticion"] == "Mensual" and r["fecha"].day == hoy.day)
        )
        existe = tareas[
            (tareas["fecha"] == hoy)
            & (tareas["tarea"] == r["tarea"])
            & (tareas["categoria"] == r["categoria"])
        ]
        if crear and existe.empty:
            nuevas.append(
                {
                    "id": new_id(),
                    "fecha": hoy,
                    "tarea": r["tarea"],
                    "categoria": r["categoria"],
                    "prioridad": r["prioridad"],
                    "repeticion": r["repeticion"],
                    "completada": False,
                }
            )
    if nuevas:
        guardar("tareas", pd.concat([tareas, pd.DataFrame(nuevas)], ignore_index=True))


def proximos_7_dias():
    hoy, fin = date.today(), date.today() + timedelta(days=7)
    filas = []
    for nombre, tipo, titulo_col, detalle_cols in [
        ("tareas", "Tarea", "tarea", ["categoria", "prioridad"]),
        ("calendario", "Evento", "titulo", ["hora", "categoria"]),
        ("universidad", "Universidad", "asignatura", ["tipo", "descripcion"]),
        ("viajes", "Viaje", "viaje", ["tipo", "descripcion"]),
    ]:
        df = cargar(nombre)
        if not df.empty and "fecha" in df.columns:
            sub = df[(df["fecha"] >= hoy) & (df["fecha"] <= fin)]
            if nombre == "tareas":
                sub = sub[~sub["completada"]]
            if "estado" in sub.columns:
                sub = sub[sub["estado"] != "Hecho"]
            for _, r in sub.iterrows():
                detalle = " | ".join(str(r.get(c, "")) for c in detalle_cols)
                filas.append(
                    {
                        "Fecha": r["fecha"],
                        "Tipo": tipo,
                        "Título": r[titulo_col],
                        "Detalle": detalle,
                    }
                )

    sus = cargar("suscripciones")
    if not sus.empty:
        for _, r in sus[sus["estado"] == "Activa"].iterrows():
            try:
                d = int(r["dia_cobro"])
                fc = date(hoy.year, hoy.month, min(max(d, 1), 28))
                if fc < hoy:
                    mes = hoy.month + 1
                    año = hoy.year + (1 if mes == 13 else 0)
                    mes = 1 if mes == 13 else mes
                    fc = date(año, mes, min(max(d, 1), 28))
                if hoy <= fc <= fin:
                    filas.append(
                        {
                            "Fecha": fc,
                            "Tipo": "Suscripción",
                            "Título": r["nombre"],
                            "Detalle": f"{r['coste']} €",
                        }
                    )
            except Exception:
                pass

    return (
        pd.DataFrame(filas).sort_values("Fecha")
        if filas
        else pd.DataFrame(columns=["Fecha", "Tipo", "Título", "Detalle"])
    )


def productividad_score():
    tareas, log, hoy = cargar("tareas"), cargar("habitos_log"), date.today()
    ult7 = [hoy - timedelta(days=i) for i in range(7)]
    tareas_7 = (
        tareas[tareas["fecha"].isin(ult7)] if not tareas.empty else pd.DataFrame()
    )
    log_7 = log[log["fecha"].isin(ult7)] if not log.empty else pd.DataFrame()
    total = len(tareas_7) + len(log_7)
    done = (tareas_7["completada"].sum() if not tareas_7.empty else 0) + (
        log_7["completado"].sum() if not log_7.empty else 0
    )
    return round(done / total * 100, 1) if total else 0


def calcular_nivel():
    tareas, objetivos, log = (
        cargar("tareas"),
        cargar("objetivos"),
        cargar("habitos_log"),
    )
    xp = 0
    if not tareas.empty:
        xp += int(tareas["completada"].sum()) * 10
    if not objetivos.empty:
        xp += len(objetivos[objetivos["estado"] == "Completado"]) * 100
    if not log.empty:
        xp += int(log["completado"].sum()) * 5
    return xp, xp // 250 + 1, xp % 250


def resumen_financiero():
    finanzas = cargar("finanzas")
    sus = cargar("suscripciones")
    presupuestos = cargar("presupuestos")
    hoy = date.today()

    if finanzas.empty:
        return {
            "ingresos": 0,
            "gastos": 0,
            "balance": 0,
            "ahorro": 0,
            "prevision": 0,
            "sus": 0,
            "top": "-",
        }

    fin_mes = finanzas[
        (pd.to_datetime(finanzas["fecha"]).dt.month == hoy.month)
        & (pd.to_datetime(finanzas["fecha"]).dt.year == hoy.year)
    ]
    ingresos = fin_mes[fin_mes["tipo"] == "Ingreso"]["cantidad"].sum()
    gastos = fin_mes[fin_mes["tipo"] == "Gasto"]["cantidad"].sum()
    balance = ingresos - gastos
    ahorro = round(balance / ingresos * 100, 1) if ingresos > 0 else 0
    prevision = round(gastos / max(hoy.day, 1) * 31, 2) if gastos > 0 else 0
    sus_coste = sus[sus["estado"] == "Activa"]["coste"].sum() if not sus.empty else 0

    gastos_df = fin_mes[fin_mes["tipo"] == "Gasto"]
    if not gastos_df.empty:
        top = (
            gastos_df.groupby("categoria")["cantidad"]
            .sum()
            .sort_values(ascending=False)
        )
        top_cat = f"{top.index[0]} · {top.iloc[0]:.0f} €"
    else:
        top_cat = "-"

    return {
        "ingresos": ingresos,
        "gastos": gastos,
        "balance": balance,
        "ahorro": ahorro,
        "prevision": prevision,
        "sus": sus_coste,
        "top": top_cat,
    }


def notificaciones():
    hoy = date.today()
    avisos = []
    tareas = cargar("tareas")
    if not tareas.empty:
        vencidas = tareas[(tareas["fecha"] < hoy) & (~tareas["completada"])]
        altas = tareas[
            (tareas["fecha"] == hoy)
            & (~tareas["completada"])
            & (tareas["prioridad"] == "Alta")
        ]
        if not vencidas.empty:
            avisos.append(
                (
                    "🔴",
                    "Tareas vencidas",
                    f"{len(vencidas)} tarea(s) pendientes de días anteriores.",
                )
            )
        if not altas.empty:
            avisos.append(
                ("🟠", "Prioridad alta", f"{len(altas)} tarea(s) importantes hoy.")
            )
    uni = cargar("universidad")
    if not uni.empty:
        prox = uni[
            (uni["fecha"] >= hoy)
            & (uni["fecha"] <= hoy + timedelta(days=7))
            & (uni["estado"] != "Hecho")
        ]
        if not prox.empty:
            avisos.append(("🎓", "Universidad", f"{len(prox)} elemento(s) próximos."))
    if not avisos:
        avisos.append(
            ("✅", "Todo en orden", "No hay alertas importantes ahora mismo.")
        )
    return avisos


def buscar(q):
    q = q.lower().strip()
    if not q:
        return pd.DataFrame()
    out = []
    for nombre in [
        "tareas",
        "notas",
        "proyectos",
        "universidad",
        "viajes",
        "wishlist",
        "calendario",
        "compras",
        "archivos",
    ]:
        df = cargar(nombre)
        for _, r in df.iterrows():
            texto = " ".join(str(x) for x in r.values).lower()
            if q in texto:
                out.append(
                    {
                        "Sección": nombre,
                        "Resultado": " | ".join(
                            str(x) for x in r.values if pd.notna(x)
                        )[:250],
                    }
                )
    return pd.DataFrame(out)


def contexto_ia():
    partes = []
    for nombre in [
        "tareas",
        "finanzas",
        "objetivos",
        "calendario",
        "universidad",
        "viajes",
        "notas",
        "proyectos",
        "wishlist",
        "suscripciones",
    ]:
        df = cargar(nombre)
        partes.append(
            f"\n--- {nombre.upper()} ---\n{df.tail(40).to_string() if not df.empty else 'Sin datos'}"
        )
    partes.append(f"\n--- PRÓXIMOS 7 DÍAS ---\n{proximos_7_dias().to_string()}")
    partes.append(f"\n--- SCORE PRODUCTIVIDAD ---\n{productividad_score()}%")
    return "\n".join(partes)


def preguntar_ia(pregunta):
    if genai is None:
        return "Falta instalar google-generativeai."
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        return "Falta configurar GEMINI_API_KEY."
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
Eres un asistente personal de productividad, organización, finanzas y estudios.
Usa los datos del usuario para responder con acciones concretas, sin inventar datos.

DATOS:
{contexto_ia()}

PREGUNTA:
{pregunta}
"""
    return model.generate_content(prompt).text


def tabla_simple(nombre):
    df = cargar(nombre)
    if df.empty:
        st.info("Sin registros.")
    else:
        st.dataframe(df, use_container_width=True)


def exportar_zip_usuario():
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        if os.path.exists(USER_DIR):
            for root, _, files in os.walk(USER_DIR):
                for file in files:
                    full = os.path.join(root, file)
                    rel = os.path.relpath(full, USER_DIR)
                    z.write(full, rel)
    buffer.seek(0)
    return buffer


def page_dashboard():
    hero("Dashboard", f"Bienvenido, {usuario_email}. Esto es lo importante de hoy.")

    hoy = date.today()
    tareas = cargar("tareas")
    wishlist = cargar("wishlist")
    compras = cargar("compras")
    habitos = cargar("habitos")
    log = cargar("habitos_log")
    fin = resumen_financiero()

    tareas_hoy = tareas[tareas["fecha"] == hoy] if not tareas.empty else pd.DataFrame()
    hechas = len(tareas_hoy[tareas_hoy["completada"]]) if not tareas_hoy.empty else 0
    total = len(tareas_hoy)
    habitos_hoy = log[log["fecha"] == hoy] if not log.empty else pd.DataFrame()
    hab_done = int(habitos_hoy["completado"].sum()) if not habitos_hoy.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        stat_card("Tareas hoy", f"{hechas}/{total}", "Completadas", "✅")
    with c2:
        stat_card("Hábitos", f"{hab_done}/{len(habitos)}", "Hechos hoy", "🏋️")
    with c3:
        stat_card(
            "Balance mes", f"{fin['balance']:.0f} €", f"Ahorro {fin['ahorro']}%", "💰"
        )
    with c4:
        pend = (
            len(wishlist[wishlist["estado"] == "Pendiente"])
            if not wishlist.empty
            else 0
        )
        comp = len(compras[compras["comprado"] == False]) if not compras.empty else 0
        stat_card("Pendientes", f"{pend + comp}", "Wishlist + compra", "🛒")

    c1, c2 = st.columns([1.25, 0.85])
    with c1:
        section_header(
            "⏰ Próximos 7 días", "Tareas, eventos, universidad, viajes y pagos."
        )
        prox = proximos_7_dias()
        if prox.empty:
            st.info("No hay eventos próximos.")
        else:
            st.dataframe(prox, use_container_width=True, hide_index=True)

    with c2:
        section_header("🔔 Avisos", "Señales rápidas para decidir qué hacer.")
        for icono, titulo, texto in notificaciones()[:5]:
            st.markdown(
                f'<div class="alert">{icono} <strong>{titulo}</strong><br><span class="small-muted">{texto}</span></div>',
                unsafe_allow_html=True,
            )

    section_header("🤖 Sugerencia rápida", "Resumen automático basado en tus datos.")
    sugerencias = []
    if total - hechas > 0:
        sugerencias.append(f"Te quedan {total-hechas} tarea(s) para hoy.")
    if fin["gastos"] > 0:
        sugerencias.append(
            f"Llevas {fin['gastos']:.0f} € gastados este mes. Categoría principal: {fin['top']}."
        )
    if not sugerencias:
        sugerencias.append("Día tranquilo. Buen momento para adelantar objetivos.")
    for s in sugerencias:
        st.write(f"- {s}")


def page_rapido():
    section_header(
        "📱 Entrada rápida", "Añade lo más común sin navegar por toda la app."
    )
    accion = st.radio("Añadir", ["Tarea", "Gasto", "Nota", "Compra"], horizontal=True)

    if accion == "Tarea":
        with st.form("quick_tarea"):
            tarea = st.text_input("Tarea")
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            if st.form_submit_button("Añadir tarea") and tarea.strip():
                add(
                    "tareas",
                    {
                        "fecha": date.today(),
                        "tarea": tarea,
                        "categoria": "Personal",
                        "prioridad": prioridad,
                        "repeticion": "No",
                        "completada": False,
                    },
                )
                st.rerun()
    elif accion == "Gasto":
        with st.form("quick_gasto"):
            cantidad = st.number_input("Cantidad (€)", min_value=0.0, step=1.0)
            categoria = st.selectbox(
                "Categoría",
                [
                    "Comida",
                    "Transporte",
                    "Ocio",
                    "Universidad",
                    "Viajes",
                    "Salud",
                    "Deporte",
                    "Otros",
                ],
            )
            desc = st.text_input("Descripción")
            if st.form_submit_button("Añadir gasto") and cantidad > 0:
                add(
                    "finanzas",
                    {
                        "fecha": date.today(),
                        "tipo": "Gasto",
                        "categoria": categoria,
                        "descripcion": desc,
                        "cantidad": cantidad,
                    },
                )
                st.rerun()
    elif accion == "Nota":
        with st.form("quick_nota"):
            nota = st.text_area("Nota")
            vinculo = st.text_input(
                "Vincular a proyecto/tema", placeholder="Ej: Erasmus, Universidad"
            )
            if st.form_submit_button("Guardar nota") and nota.strip():
                add(
                    "notas",
                    {
                        "fecha": date.today(),
                        "titulo": "Nota rápida",
                        "nota": nota,
                        "categoria": "Recordatorio",
                        "vinculo": vinculo,
                    },
                )
                st.rerun()
    else:
        with st.form("quick_compra"):
            item = st.text_input("Producto")
            if st.form_submit_button("Añadir compra") and item.strip():
                add(
                    "compras",
                    {
                        "item": item,
                        "categoria": "Comida",
                        "cantidad": "",
                        "comprado": False,
                    },
                )
                st.rerun()

    section_header("✅ Tareas de hoy")
    tareas = cargar("tareas")
    hoy_df = (
        tareas[tareas["fecha"] == date.today()] if not tareas.empty else pd.DataFrame()
    )
    if hoy_df.empty:
        st.info("No tienes tareas para hoy.")
    else:
        for _, r in hoy_df.iterrows():
            check = st.checkbox(
                r["tarea"], value=bool(r["completada"]), key=f"quick_{r['id']}"
            )
            if check != r["completada"]:
                update("tareas", r["id"], {"completada": check})
                st.rerun()


def page_productividad():
    vista = st.radio(
        "Productividad",
        ["Tareas", "Hábitos", "Objetivos", "Proyectos"],
        horizontal=True,
    )

    if vista == "Tareas":
        section_header("✅ Tareas", "Planifica, completa y edita tareas.")
        with st.form("form_tarea"):
            c1, c2, c3 = st.columns(3)
            fecha = c1.date_input("Fecha", value=date.today())
            categoria = c2.selectbox(
                "Categoría",
                [
                    "Personal",
                    "Universidad",
                    "Trabajo",
                    "Deporte",
                    "Casa",
                    "Erasmus",
                    "Otro",
                ],
            )
            prioridad = c3.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            tarea = st.text_input("Tarea")
            repeticion = st.selectbox(
                "Repetición", ["No", "Diaria", "Semanal", "Mensual"]
            )
            if st.form_submit_button("Añadir") and tarea.strip():
                add(
                    "tareas",
                    {
                        "fecha": fecha,
                        "tarea": tarea,
                        "categoria": categoria,
                        "prioridad": prioridad,
                        "repeticion": repeticion,
                        "completada": False,
                    },
                )
                st.rerun()

        tareas = cargar("tareas")
        fecha_ver = st.date_input("Ver día", value=date.today(), key="fecha_tareas")
        if tareas.empty:
            st.info("No hay tareas.")
        else:
            for _, r in tareas[tareas["fecha"] == fecha_ver].iterrows():
                with st.expander(f"{'✅' if r['completada'] else '⬜'} {r['tarea']}"):
                    nueva_tarea = st.text_input(
                        "Tarea", value=r["tarea"], key=f"txt_{r['id']}"
                    )
                    nueva_fecha = st.date_input(
                        "Fecha", value=r["fecha"], key=f"fecha_{r['id']}"
                    )
                    done = st.checkbox(
                        "Completada", value=bool(r["completada"]), key=f"done_{r['id']}"
                    )
                    c1, c2 = st.columns(2)
                    if c1.button("Guardar", key=f"save_{r['id']}"):
                        update(
                            "tareas",
                            r["id"],
                            {
                                "fecha": nueva_fecha,
                                "tarea": nueva_tarea,
                                "completada": done,
                            },
                        )
                        st.rerun()
                    if c2.button("Eliminar", key=f"del_{r['id']}"):
                        delete("tareas", r["id"])
                        st.rerun()
            st.dataframe(
                tareas.sort_values("fecha", ascending=False), use_container_width=True
            )

    elif vista == "Hábitos":
        section_header("🏋️ Hábitos", "Marca hábitos diarios o semanales.")
        with st.form("form_habito"):
            habito = st.text_input("Nuevo hábito")
            c1, c2 = st.columns(2)
            categoria = c1.selectbox(
                "Categoría", ["Salud", "Estudio", "Deporte", "Casa", "Personal", "Otro"]
            )
            frecuencia = c2.selectbox("Frecuencia", ["Diaria", "Semanal"])
            if st.form_submit_button("Crear") and habito.strip():
                add(
                    "habitos",
                    {
                        "habito": habito,
                        "categoria": categoria,
                        "frecuencia": frecuencia,
                    },
                )
                st.rerun()

        habitos, log, hoy = cargar("habitos"), cargar("habitos_log"), date.today()
        if habitos.empty:
            st.info("No hay hábitos.")
        else:
            for _, h in habitos.iterrows():
                ya = log[(log["fecha"] == hoy) & (log["habito_id"] == h["id"])]
                completado = False if ya.empty else bool(ya.iloc[0]["completado"])
                c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
                check = c1.checkbox("", value=completado, key=f"hab_{h['id']}")
                c2.markdown(f"**{h['habito']}**")
                c2.caption(f"{h['categoria']} · {h['frecuencia']}")
                if c3.button("🗑️", key=f"del_hab_{h['id']}"):
                    delete("habitos", h["id"])
                    st.rerun()
                if check != completado:
                    if ya.empty:
                        add(
                            "habitos_log",
                            {"fecha": hoy, "habito_id": h["id"], "completado": check},
                        )
                    else:
                        update("habitos_log", ya.iloc[0]["id"], {"completado": check})
                    st.rerun()

    elif vista == "Objetivos":
        section_header("🎯 Objetivos", "Metas con progreso y fecha límite.")
        with st.form("form_obj"):
            obj = st.text_input("Objetivo")
            c1, c2, c3 = st.columns(3)
            cat = c1.selectbox(
                "Categoría",
                [
                    "Personal",
                    "Estudios",
                    "Deporte",
                    "Dinero",
                    "Viajes",
                    "Trabajo",
                    "Otro",
                ],
            )
            prog = c2.slider("Progreso", 0, 100, 0)
            est = c3.selectbox("Estado", ["Activo", "Completado", "Pausado"])
            fecha = st.date_input("Fecha límite", value=date.today())
            if st.form_submit_button("Guardar") and obj.strip():
                add(
                    "objetivos",
                    {
                        "objetivo": obj,
                        "categoria": cat,
                        "progreso": prog,
                        "fecha_limite": fecha,
                        "estado": est,
                    },
                )
                st.rerun()
        df = cargar("objetivos")
        if not df.empty:
            for _, r in df.iterrows():
                st.progress(float(r["progreso"]) / 100)
                st.write(
                    f"**{r['objetivo']}** · {r['categoria']} · {r['estado']} · {r['fecha_limite']}"
                )
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay objetivos.")

    else:
        section_header("📚 Proyectos", "Divide proyectos en tareas.")
        with st.form("form_proy"):
            proy = st.text_input("Proyecto")
            tarea = st.text_input("Tarea")
            estado = st.selectbox("Estado", ["Pendiente", "En curso", "Hecho"])
            pr = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            if st.form_submit_button("Añadir") and proy.strip() and tarea.strip():
                add(
                    "proyectos",
                    {
                        "proyecto": proy,
                        "tarea": tarea,
                        "estado": estado,
                        "prioridad": pr,
                    },
                )
                st.rerun()
        df = cargar("proyectos")
        if df.empty:
            st.info("No hay proyectos.")
        else:
            for p in df["proyecto"].unique():
                st.markdown(f"### {p}")
                st.dataframe(df[df["proyecto"] == p], use_container_width=True)


def page_finanzas():
    vista = st.radio(
        "Finanzas",
        ["Dashboard", "Movimientos", "Presupuestos", "Suscripciones", "Wishlist"],
        horizontal=True,
    )

    fin = resumen_financiero()
    if vista == "Dashboard":
        section_header("💰 Finanzas", "Estado mensual, previsión y categorías.")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            stat_card("Ingresos", f"{fin['ingresos']:.0f} €", "Este mes", "📈")
        with c2:
            stat_card("Gastos", f"{fin['gastos']:.0f} €", "Este mes", "📉")
        with c3:
            stat_card(
                "Balance", f"{fin['balance']:.0f} €", f"Ahorro {fin['ahorro']}%", "💰"
            )
        with c4:
            stat_card(
                "Previsión gasto",
                f"{fin['prevision']:.0f} €",
                "Estimación mensual",
                "🔮",
            )

        finanzas = cargar("finanzas")
        if not finanzas.empty:
            hoy = date.today()
            fin_mes = finanzas[
                (pd.to_datetime(finanzas["fecha"]).dt.month == hoy.month)
                & (pd.to_datetime(finanzas["fecha"]).dt.year == hoy.year)
            ]
            gastos_df = fin_mes[fin_mes["tipo"] == "Gasto"]
            if not gastos_df.empty:
                st.plotly_chart(
                    px.pie(
                        gastos_df,
                        names="categoria",
                        values="cantidad",
                        title="Gastos por categoría",
                    ),
                    use_container_width=True,
                )

    elif vista == "Movimientos":
        section_header("💳 Movimientos", "Añade ingresos y gastos.")
        with st.form("form_fin"):
            c1, c2, c3 = st.columns(3)
            fecha = c1.date_input("Fecha", value=date.today(), key="fecha_fin")
            tipo = c2.selectbox("Tipo", ["Gasto", "Ingreso"])
            cantidad = c3.number_input("Cantidad (€)", min_value=0.0, step=1.0)
            categoria = st.selectbox(
                "Categoría",
                [
                    "Comida",
                    "Transporte",
                    "Ocio",
                    "Universidad",
                    "Viajes",
                    "Salud",
                    "Deporte",
                    "Ingresos",
                    "Otros",
                ],
            )
            desc = st.text_input("Descripción")
            if st.form_submit_button("Guardar") and cantidad > 0:
                add(
                    "finanzas",
                    {
                        "fecha": fecha,
                        "tipo": tipo,
                        "categoria": categoria,
                        "descripcion": desc,
                        "cantidad": cantidad,
                    },
                )
                st.rerun()
        tabla_simple("finanzas")

    elif vista == "Presupuestos":
        section_header("📊 Presupuestos", "Controla límites por categoría.")
        presupuestos = cargar("presupuestos")
        finanzas = cargar("finanzas")
        with st.form("form_pres"):
            c1, c2 = st.columns(2)
            cat = c1.selectbox(
                "Categoría presupuesto",
                [
                    "Comida",
                    "Transporte",
                    "Ocio",
                    "Universidad",
                    "Viajes",
                    "Salud",
                    "Deporte",
                    "Otros",
                ],
            )
            lim = c2.number_input("Límite mensual (€)", min_value=0.0, step=10.0)
            if st.form_submit_button("Guardar presupuesto") and lim > 0:
                viejo = presupuestos[presupuestos["categoria"] == cat]
                if viejo.empty:
                    add("presupuestos", {"categoria": cat, "limite_mensual": lim})
                else:
                    update("presupuestos", viejo.iloc[0]["id"], {"limite_mensual": lim})
                st.rerun()
        if not presupuestos.empty:
            hoy = date.today()
            fin_mes = (
                finanzas[
                    (pd.to_datetime(finanzas["fecha"]).dt.month == hoy.month)
                    & (pd.to_datetime(finanzas["fecha"]).dt.year == hoy.year)
                ]
                if not finanzas.empty
                else pd.DataFrame()
            )
            gastos_mes = (
                fin_mes[fin_mes["tipo"] == "Gasto"]
                .groupby("categoria", as_index=False)["cantidad"]
                .sum()
                if not fin_mes.empty
                else pd.DataFrame(columns=["categoria", "cantidad"])
            )
            control = presupuestos.merge(gastos_mes, on="categoria", how="left").fillna(
                {"cantidad": 0}
            )
            control["restante"] = control["limite_mensual"] - control["cantidad"]
            control["uso_%"] = (
                control["cantidad"] / control["limite_mensual"] * 100
            ).round(1)
            st.dataframe(control, use_container_width=True)
        else:
            st.info("No hay presupuestos.")

    elif vista == "Suscripciones":
        section_header("💳 Suscripciones", "Pagos recurrentes.")
        with st.form("form_sus"):
            nombre = st.text_input("Nombre")
            c1, c2, c3 = st.columns(3)
            cat = c1.selectbox(
                "Categoría",
                ["Streaming", "Software", "Deporte", "Estudios", "Servicios", "Otro"],
            )
            coste = c2.number_input("Coste mensual (€)", min_value=0.0, step=1.0)
            dia = c3.number_input("Día cobro", min_value=1, max_value=31, value=1)
            estado = st.selectbox("Estado", ["Activa", "Pausada", "Cancelada"])
            if st.form_submit_button("Añadir") and nombre.strip():
                add(
                    "suscripciones",
                    {
                        "nombre": nombre,
                        "categoria": cat,
                        "coste": coste,
                        "dia_cobro": dia,
                        "estado": estado,
                    },
                )
                st.rerun()
        df = cargar("suscripciones")
        if not df.empty:
            st.metric(
                "Coste mensual activo",
                f"{df[df['estado']=='Activa']['coste'].sum():.2f} €",
            )
        tabla_simple("suscripciones")

    else:
        section_header("⭐ Wishlist", "Lista de deseos con precio.")
        with st.form("form_wish"):
            item = st.text_input("Nombre")
            precio = st.number_input("Precio (€)", min_value=0.0, step=1.0)
            pr = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            est = st.selectbox("Estado", ["Pendiente", "Comprado", "Descartado"])
            url = st.text_input("URL")
            if st.form_submit_button("Añadir") and item.strip():
                add(
                    "wishlist",
                    {
                        "nombre": item,
                        "precio": precio,
                        "prioridad": pr,
                        "estado": est,
                        "url": url,
                    },
                )
                st.rerun()
        df = cargar("wishlist")
        if not df.empty:
            st.metric(
                "Total pendiente",
                f"{df[df['estado']=='Pendiente']['precio'].sum():.2f} €",
            )
        tabla_simple("wishlist")


def page_vida():
    vista = st.radio(
        "Vida", ["Calendario", "Universidad", "Viajes", "Compras"], horizontal=True
    )

    if vista == "Calendario":
        section_header("📅 Calendario", "Eventos y recordatorios.")
        with st.form("form_evento"):
            c1, c2 = st.columns(2)
            fecha = c1.date_input("Fecha", value=date.today(), key="fecha_evento")
            hora = c2.text_input("Hora", placeholder="Ej: 18:30")
            titulo = st.text_input("Título")
            categoria = st.selectbox(
                "Categoría",
                ["Personal", "Universidad", "Trabajo", "Viaje", "Cita", "Otro"],
            )
            notas = st.text_area("Notas")
            if st.form_submit_button("Añadir") and titulo.strip():
                add(
                    "calendario",
                    {
                        "fecha": fecha,
                        "hora": hora,
                        "titulo": titulo,
                        "categoria": categoria,
                        "notas": notas,
                    },
                )
                st.rerun()
        tabla_simple("calendario")

    elif vista == "Universidad":
        section_header("🎓 Universidad", "Exámenes, prácticas y entregas.")
        with st.form("form_uni"):
            asig = st.text_input("Asignatura")
            c1, c2, c3 = st.columns(3)
            tipo = c1.selectbox(
                "Tipo", ["Examen", "Práctica", "Trabajo", "Clase", "Entrega", "Otro"]
            )
            fecha = c2.date_input("Fecha", value=date.today())
            pr = c3.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            desc = st.text_input("Descripción")
            est = st.selectbox("Estado", ["Pendiente", "En curso", "Hecho"])
            if st.form_submit_button("Guardar") and asig.strip():
                add(
                    "universidad",
                    {
                        "asignatura": asig,
                        "tipo": tipo,
                        "descripcion": desc,
                        "fecha": fecha,
                        "estado": est,
                        "prioridad": pr,
                    },
                )
                st.rerun()
        tabla_simple("universidad")

    elif vista == "Viajes":
        section_header("✈️ Viajes", "Checklist, costes y documentos.")
        with st.form("form_viaje"):
            viaje = st.text_input("Viaje")
            c1, c2, c3 = st.columns(3)
            tipo = c1.selectbox(
                "Tipo",
                [
                    "Vuelo",
                    "Alojamiento",
                    "Transporte",
                    "Checklist",
                    "Gasto",
                    "Documento",
                    "Otro",
                ],
            )
            fecha = c2.date_input("Fecha", value=date.today())
            coste = c3.number_input("Coste (€)", min_value=0.0, step=1.0)
            desc = st.text_input("Descripción")
            est = st.selectbox("Estado", ["Pendiente", "Reservado", "Pagado", "Hecho"])
            if st.form_submit_button("Guardar") and viaje.strip():
                add(
                    "viajes",
                    {
                        "viaje": viaje,
                        "tipo": tipo,
                        "descripcion": desc,
                        "fecha": fecha,
                        "coste": coste,
                        "estado": est,
                    },
                )
                st.rerun()
        df = cargar("viajes")
        if not df.empty:
            st.metric("Coste total", f"{df['coste'].sum():.2f} €")
        tabla_simple("viajes")

    else:
        section_header("🛒 Compras", "Lista rápida de compra.")
        with st.form("form_compra"):
            item = st.text_input("Producto")
            cat = st.selectbox(
                "Categoría",
                ["Comida", "Casa", "Higiene", "Deporte", "Universidad", "Otro"],
            )
            cant = st.text_input("Cantidad")
            if st.form_submit_button("Añadir") and item.strip():
                add(
                    "compras",
                    {
                        "item": item,
                        "categoria": cat,
                        "cantidad": cant,
                        "comprado": False,
                    },
                )
                st.rerun()
        df = cargar("compras")
        if df.empty:
            st.info("Lista vacía.")
        else:
            for _, r in df.iterrows():
                check = st.checkbox(
                    f"{r['item']} ({r['cantidad']})",
                    value=bool(r["comprado"]),
                    key=f"compr_{r['id']}",
                )
                if check != r["comprado"]:
                    update("compras", r["id"], {"comprado": check})
                    st.rerun()


def page_conocimiento():
    vista = st.radio("Conocimiento", ["Notas", "Archivos", "Buscar"], horizontal=True)

    if vista == "Notas":
        section_header("📝 Notas", "Ideas, recordatorios y apuntes.")
        with st.form("form_nota"):
            titulo = st.text_input("Título")
            cat = st.selectbox(
                "Categoría",
                ["Idea", "Recordatorio", "Universidad", "Proyecto", "Personal", "Otro"],
            )
            vinculo = st.text_input(
                "Vincular a proyecto/tema", placeholder="Ej: Erasmus, Universidad"
            )
            nota = st.text_area("Nota")
            if st.form_submit_button("Guardar") and nota.strip():
                add(
                    "notas",
                    {
                        "fecha": date.today(),
                        "titulo": titulo,
                        "nota": nota,
                        "categoria": cat,
                        "vinculo": vinculo,
                    },
                )
                st.rerun()
        df = cargar("notas")
        if df.empty:
            st.info("No hay notas.")
        else:
            for _, r in df.sort_values("fecha", ascending=False).iterrows():
                with st.expander(f"{r['fecha']} - {r['titulo']}"):
                    st.caption(f"{r['categoria']} · Vínculo: {r.get('vinculo', '')}")
                    st.write(r["nota"])

    elif vista == "Archivos":
        section_header("📂 Archivos", "Metadatos en nube. Storage completo pendiente.")
        st.warning(
            "Los metadatos se sincronizan en Supabase. Los archivos físicos todavía se guardan localmente."
        )
        with st.form("form_archivo"):
            archivo = st.file_uploader("Subir archivo")
            categoria = st.selectbox(
                "Categoría",
                ["Universidad", "Viaje", "Proyecto", "Personal", "Finanzas", "Otro"],
            )
            vinculo = st.text_input(
                "Vincular a proyecto/tema", placeholder="Ej: Erasmus, Empresa"
            )
            subir = st.form_submit_button("Guardar archivo")
            if subir and archivo is not None:
                safe_name = f"{str(uuid.uuid4())[:8]}_{archivo.name}"
                ruta = os.path.join(FILES_DIR, safe_name)
                with open(ruta, "wb") as f:
                    f.write(archivo.getbuffer())
                add(
                    "archivos",
                    {
                        "fecha": date.today(),
                        "nombre": archivo.name,
                        "categoria": categoria,
                        "vinculo": vinculo,
                        "ruta": ruta,
                    },
                )
                st.rerun()
        tabla_simple("archivos")

    else:
        section_header("🔎 Buscar", "Busca en toda tu información.")
        q = st.text_input("Buscar")
        res = buscar(q)
        if q and res.empty:
            st.info("No se encontraron resultados.")
        elif not res.empty:
            st.dataframe(res, use_container_width=True)


def page_ia():
    section_header(
        "🤖 Asistente IA",
        "Pregunta sobre tus tareas, finanzas, estudios y planificación.",
    )
    pregunta = st.text_area(
        "Pregunta", placeholder="Ej: ¿Qué debería priorizar esta semana?"
    )
    if st.button("Preguntar") and pregunta.strip():
        with st.spinner("Analizando tus datos..."):
            st.markdown(preguntar_ia(pregunta))


def page_estadisticas():
    section_header("📊 Estadísticas", "Rendimiento personal y finanzas.")
    tareas, finanzas, objetivos, log = (
        cargar("tareas"),
        cargar("finanzas"),
        cargar("objetivos"),
        cargar("habitos_log"),
    )
    xp, nivel, resto = calcular_nivel()
    c1, c2, c3 = st.columns(3)
    with c1:
        stat_card("Nivel", nivel, f"{xp} XP total", "🏆")
    with c2:
        stat_card("Productividad", f"{productividad_score()}%", "Últimos 7 días", "📊")
    with c3:
        stat_card("Progreso nivel", f"{resto}/250", "XP restante", "⚡")

    if not tareas.empty:
        comp = tareas["completada"].sum()
        st.plotly_chart(
            px.bar(
                tareas.groupby("fecha", as_index=False)["completada"].sum(),
                x="fecha",
                y="completada",
                title="Tareas completadas por día",
            ),
            use_container_width=True,
        )
    if not finanzas.empty:
        f = finanzas.copy()
        f["mes"] = pd.to_datetime(f["fecha"]).dt.to_period("M").astype(str)
        st.plotly_chart(
            px.bar(
                f.groupby(["mes", "tipo"], as_index=False)["cantidad"].sum(),
                x="mes",
                y="cantidad",
                color="tipo",
                barmode="group",
                title="Ingresos vs gastos",
            ),
            use_container_width=True,
        )
    if not objetivos.empty:
        st.plotly_chart(
            px.bar(
                objetivos,
                x="objetivo",
                y="progreso",
                color="categoria",
                title="Progreso objetivos",
            ),
            use_container_width=True,
        )
    if not log.empty:
        st.plotly_chart(
            px.line(
                log.groupby("fecha", as_index=False)["completado"].sum(),
                x="fecha",
                y="completado",
                markers=True,
                title="Hábitos por día",
            ),
            use_container_width=True,
        )


def page_ajustes():
    section_header("⚙️ Ajustes", "Sesión, copias y sincronización.")
    st.success("Datos principales sincronizados en Supabase.")
    st.download_button(
        "Descargar copia ZIP local",
        data=exportar_zip_usuario(),
        file_name=f"life_os_backup_{slug(usuario_email)}.zip",
        mime="application/zip",
    )
    st.caption(
        "El ZIP es una copia local de respaldo. Los datos principales viven en Supabase."
    )


generar_repeticiones()


# ============================================================
# SIDEBAR NAV
# ============================================================

st.sidebar.markdown(
    f"""
    <div class="sidebar-brand">
        <div class="sidebar-brand-title">LIFE OS</div>
        <div class="sidebar-brand-sub">{usuario_email}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

xp, nivel, resto = calcular_nivel()
st.sidebar.metric("Nivel", nivel)
st.sidebar.progress(resto / 250)
st.sidebar.caption(f"XP total: {xp}")

st.sidebar.divider()
st.sidebar.subheader("🔔 Avisos")
for icono, titulo, texto in notificaciones()[:4]:
    st.sidebar.markdown(f"**{icono} {titulo}**")
    st.sidebar.caption(texto)

st.sidebar.divider()
if st.sidebar.button("Cerrar sesión"):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.clear()
    st.rerun()


# ============================================================
# NAVEGACIÓN PRINCIPAL SIEMPRE VISIBLE
# ============================================================

opciones_nav = [
    "🏠 Dashboard",
    "📱 Rápido",
    "📋 Productividad",
    "💰 Finanzas",
    "🎓 Vida",
    "🧠 Conocimiento",
    "📊 Estadísticas",
    "🤖 IA",
    "⚙️ Ajustes",
]

if "nav_principal" not in st.session_state:
    st.session_state["nav_principal"] = "🏠 Dashboard"

st.markdown(
    """
    <div class="top-nav-wrap">
        <div class="nav-help">Navegación principal</div>
    </div>
    """,
    unsafe_allow_html=True,
)

nav = st.radio(
    "Navegación principal",
    opciones_nav,
    index=(
        opciones_nav.index(st.session_state["nav_principal"])
        if st.session_state["nav_principal"] in opciones_nav
        else 0
    ),
    horizontal=True,
    label_visibility="collapsed",
)

st.session_state["nav_principal"] = nav

st.divider()


# ============================================================
# ROUTER
# ============================================================

if nav == "🏠 Dashboard":
    page_dashboard()
elif nav == "📱 Rápido":
    page_rapido()
elif nav == "📋 Productividad":
    page_productividad()
elif nav == "💰 Finanzas":
    page_finanzas()
elif nav == "🎓 Vida":
    page_vida()
elif nav == "🧠 Conocimiento":
    page_conocimiento()
elif nav == "📊 Estadísticas":
    page_estadisticas()
elif nav == "🤖 IA":
    page_ia()
elif nav == "⚙️ Ajustes":
    page_ajustes()
