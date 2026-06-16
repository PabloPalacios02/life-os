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

st.set_page_config(page_title="LIFE OS", page_icon="✅", layout="wide")

APP_NAME = "✅ LIFE OS"
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
    except Exception as e:
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


def usuarios_disponibles():
    usuarios = set()
    try:
        res = supabase.table("life_os_items").select("user_id").execute()
        for r in res.data or []:
            if r.get("user_id"):
                usuarios.add(r["user_id"])
    except Exception:
        pass
    if os.path.exists(BASE_DATA_DIR):
        for d in os.listdir(BASE_DATA_DIR):
            if os.path.isdir(os.path.join(BASE_DATA_DIR, d)):
                usuarios.add(d)
    if not usuarios:
        usuarios.add("pablo")
    return sorted(usuarios)


st.sidebar.title(APP_NAME)
st.sidebar.caption("Centro personal multiusuario en la nube")
usuarios = usuarios_disponibles()
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = usuarios[0]
usuario_actual = st.sidebar.selectbox(
    "Usuario",
    usuarios,
    index=(
        usuarios.index(st.session_state["usuario_actual"])
        if st.session_state["usuario_actual"] in usuarios
        else 0
    ),
)
st.session_state["usuario_actual"] = usuario_actual

nuevo_usuario = st.sidebar.text_input("Crear nuevo usuario")
if st.sidebar.button("Crear usuario") and nuevo_usuario.strip():
    nuevo = slug(nuevo_usuario)
    st.session_state["usuario_actual"] = nuevo
    os.makedirs(os.path.join(BASE_DATA_DIR, nuevo, "archivos"), exist_ok=True)
    usuario_actual = nuevo
    add("config", {"clave": "usuario_creado", "valor": "true"})
    st.rerun()

USER_DIR = os.path.join(BASE_DATA_DIR, usuario_actual)
FILES_DIR = os.path.join(USER_DIR, "archivos")
os.makedirs(FILES_DIR, exist_ok=True)
st.sidebar.success(f"Usuario activo: {usuario_actual}")


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
            if nombre in ["tareas"]:
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


def sugerencia_diaria():
    prox = proximos_7_dias()
    tareas, finanzas, presupuestos = (
        cargar("tareas"),
        cargar("finanzas"),
        cargar("presupuestos"),
    )
    hoy = date.today()
    mensajes = []
    if not prox.empty:
        mensajes.append(
            f"Tienes {len(prox)} elementos importantes en los próximos 7 días."
        )
    tareas_hoy = (
        tareas[(tareas["fecha"] == hoy) & (~tareas["completada"])]
        if not tareas.empty
        else pd.DataFrame()
    )
    if not tareas_hoy.empty:
        alta = tareas_hoy[tareas_hoy["prioridad"] == "Alta"]
        mensajes.append(
            f"Prioriza {len(alta)} tarea(s) de prioridad alta hoy."
            if not alta.empty
            else f"Tienes {len(tareas_hoy)} tarea(s) pendientes hoy."
        )
    if not finanzas.empty and not presupuestos.empty:
        fin_mes = finanzas[
            (pd.to_datetime(finanzas["fecha"]).dt.month == hoy.month)
            & (pd.to_datetime(finanzas["fecha"]).dt.year == hoy.year)
            & (finanzas["tipo"] == "Gasto")
        ]
        gastos_mes = fin_mes.groupby("categoria", as_index=False)["cantidad"].sum()
        control = presupuestos.merge(gastos_mes, on="categoria", how="left").fillna(
            {"cantidad": 0}
        )
        if not control[control["cantidad"] > control["limite_mensual"]].empty:
            mensajes.append("Has superado algún presupuesto mensual. Revisa Finanzas.")
    return mensajes or [
        "Día tranquilo. Buen momento para adelantar objetivos o limpiar tareas antiguas."
    ]


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
        return "Falta instalar google-generativeai: pip install google-generativeai"
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        return "Falta configurar GEMINI_API_KEY en .streamlit/secrets.toml"
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


generar_repeticiones()

st.title(APP_NAME)
st.caption(
    "Tareas, dinero, hábitos, universidad, viajes, archivos, segundo cerebro e IA sincronizados en Supabase."
)
for m in sugerencia_diaria():
    st.sidebar.info(m)
xp, nivel, resto = calcular_nivel()
st.sidebar.metric("Nivel", nivel)
st.sidebar.progress(resto / 250)
st.sidebar.caption(f"XP total: {xp}")

tabs = st.tabs(
    [
        "📱 Rápido",
        "🏠 Inicio",
        "🔎 Buscar",
        "✅ Tareas",
        "📅 Calendario",
        "🏋️ Hábitos",
        "💰 Finanzas",
        "💳 Suscripciones",
        "⭐ Wishlist",
        "🛒 Compras",
        "🎯 Objetivos",
        "📚 Proyectos",
        "🎓 Universidad",
        "✈️ Viajes",
        "📝 Notas",
        "📂 Archivos",
        "🧠 Cerebro",
        "📊 Estadísticas",
        "☁️ Copias/Nube",
        "🤖 IA",
    ]
)

with tabs[0]:
    st.subheader("📱 Entrada rápida")
    accion = st.radio("Añadir", ["Tarea", "Gasto", "Nota", "Compra"], horizontal=True)
    if accion == "Tarea":
        with st.form("quick_tarea"):
            tarea = st.text_input("Tarea")
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            if st.form_submit_button("Añadir") and tarea.strip():
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
            if st.form_submit_button("Añadir") and cantidad > 0:
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
                "Vincular a proyecto/tema",
                placeholder="Ej: RUNATICS, Erasmus, Universidad",
            )
            if st.form_submit_button("Guardar") and nota.strip():
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
            if st.form_submit_button("Añadir") and item.strip():
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
    st.divider()
    st.subheader("Tareas de hoy")
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

with tabs[1]:
    st.subheader("🏠 Panel principal")
    hoy = date.today()
    tareas, finanzas, wishlist, compras, habitos, log = (
        cargar("tareas"),
        cargar("finanzas"),
        cargar("wishlist"),
        cargar("compras"),
        cargar("habitos"),
        cargar("habitos_log"),
    )
    tareas_hoy = tareas[tareas["fecha"] == hoy] if not tareas.empty else pd.DataFrame()
    hechas, total = (
        (len(tareas_hoy[tareas_hoy["completada"]]), len(tareas_hoy))
        if not tareas_hoy.empty
        else (0, 0)
    )
    fin_mes = (
        finanzas[
            (pd.to_datetime(finanzas["fecha"]).dt.month == hoy.month)
            & (pd.to_datetime(finanzas["fecha"]).dt.year == hoy.year)
        ]
        if not finanzas.empty
        else pd.DataFrame()
    )
    ingresos = (
        fin_mes[fin_mes["tipo"] == "Ingreso"]["cantidad"].sum()
        if not fin_mes.empty
        else 0
    )
    gastos = (
        fin_mes[fin_mes["tipo"] == "Gasto"]["cantidad"].sum()
        if not fin_mes.empty
        else 0
    )
    habitos_hoy = log[log["fecha"] == hoy] if not log.empty else pd.DataFrame()
    hab_done = habitos_hoy["completado"].sum() if not habitos_hoy.empty else 0
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("✅ Tareas hoy", f"{hechas}/{total}")
    c2.metric("🏋️ Hábitos hoy", f"{int(hab_done)}/{len(habitos)}")
    c3.metric("💸 Gastos mes", f"{gastos:.2f} €")
    c4.metric("💰 Balance mes", f"{ingresos-gastos:.2f} €")
    c5.metric(
        "⭐ Wishlist",
        len(wishlist[wishlist["estado"] == "Pendiente"]) if not wishlist.empty else 0,
    )
    c6.metric("📊 Productividad", f"{productividad_score()}%")
    st.subheader("⏰ Próximos 7 días")
    st.dataframe(proximos_7_dias(), use_container_width=True)
    st.subheader("🤖 Resumen inteligente")
    for m in sugerencia_diaria():
        st.write(f"- {m}")

with tabs[2]:
    st.subheader("🔎 Buscador global")
    q = st.text_input(
        "Buscar en tareas, notas, proyectos, universidad, viajes, wishlist, compras, calendario y archivos"
    )
    res = buscar(q)
    if q and res.empty:
        st.info("No se encontraron resultados.")
    elif not res.empty:
        st.dataframe(res, use_container_width=True)

with tabs[3]:
    st.subheader("✅ Tareas")
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
        repeticion = st.selectbox("Repetición", ["No", "Diaria", "Semanal", "Mensual"])
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

with tabs[4]:
    st.subheader("📅 Calendario")
    with st.form("form_evento"):
        c1, c2 = st.columns(2)
        fecha = c1.date_input("Fecha", value=date.today(), key="fecha_evento")
        hora = c2.text_input("Hora", placeholder="Ej: 18:30")
        titulo = st.text_input("Título")
        categoria = st.selectbox(
            "Categoría", ["Personal", "Universidad", "Trabajo", "Viaje", "Cita", "Otro"]
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

with tabs[5]:
    st.subheader("🏋️ Hábitos")
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
                {"habito": habito, "categoria": categoria, "frecuencia": frecuencia},
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
            c2.write(f"**{h['habito']}**")
            c2.caption(f"{h['categoria']} | {h['frecuencia']}")
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

with tabs[6]:
    st.subheader("💰 Finanzas")
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
    finanzas, presupuestos = cargar("finanzas"), cargar("presupuestos")
    with st.expander("Configurar presupuestos mensuales"):
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
    if finanzas.empty:
        st.info("Sin movimientos.")
    else:
        hoy = date.today()
        fin_mes = finanzas[
            (pd.to_datetime(finanzas["fecha"]).dt.month == hoy.month)
            & (pd.to_datetime(finanzas["fecha"]).dt.year == hoy.year)
        ]
        ingresos = fin_mes[fin_mes["tipo"] == "Ingreso"]["cantidad"].sum()
        gastos = fin_mes[fin_mes["tipo"] == "Gasto"]["cantidad"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Ingresos mes", f"{ingresos:.2f} €")
        c2.metric("Gastos mes", f"{gastos:.2f} €")
        c3.metric("Balance", f"{ingresos-gastos:.2f} €")
        if not presupuestos.empty:
            gastos_mes = (
                fin_mes[fin_mes["tipo"] == "Gasto"]
                .groupby("categoria", as_index=False)["cantidad"]
                .sum()
            )
            control = presupuestos.merge(gastos_mes, on="categoria", how="left").fillna(
                {"cantidad": 0}
            )
            control["restante"] = control["limite_mensual"] - control["cantidad"]
            control["uso_%"] = (
                control["cantidad"] / control["limite_mensual"] * 100
            ).round(1)
            st.subheader("Control de presupuestos")
            st.dataframe(control, use_container_width=True)
        gastos_df = fin_mes[fin_mes["tipo"] == "Gasto"]
        if not gastos_df.empty:
            st.plotly_chart(
                px.pie(
                    gastos_df,
                    names="categoria",
                    values="cantidad",
                    title="Gastos del mes",
                ),
                use_container_width=True,
            )
        st.dataframe(
            finanzas.sort_values("fecha", ascending=False), use_container_width=True
        )


def seccion_suscripciones():
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
            "Coste mensual activo", f"{df[df['estado']=='Activa']['coste'].sum():.2f} €"
        )
        st.metric(
            "Coste anual activo",
            f"{df[df['estado']=='Activa']['coste'].sum()*12:.2f} €",
        )
    tabla_simple("suscripciones")


def seccion_wishlist():
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
            "Total pendiente", f"{df[df['estado']=='Pendiente']['precio'].sum():.2f} €"
        )
    tabla_simple("wishlist")


def seccion_compras():
    with st.form("form_compra"):
        item = st.text_input("Producto")
        cat = st.selectbox(
            "Categoría", ["Comida", "Casa", "Higiene", "Deporte", "Universidad", "Otro"]
        )
        cant = st.text_input("Cantidad")
        if st.form_submit_button("Añadir") and item.strip():
            add(
                "compras",
                {"item": item, "categoria": cat, "cantidad": cant, "comprado": False},
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


def seccion_objetivos():
    with st.form("form_obj"):
        obj = st.text_input("Objetivo")
        c1, c2, c3 = st.columns(3)
        cat = c1.selectbox(
            "Categoría",
            ["Personal", "Estudios", "Deporte", "Dinero", "Viajes", "Trabajo", "Otro"],
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
    tabla_simple("objetivos")


def seccion_proyectos():
    with st.form("form_proy"):
        proy = st.text_input("Proyecto")
        tarea = st.text_input("Tarea")
        estado = st.selectbox("Estado", ["Pendiente", "En curso", "Hecho"])
        pr = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
        if st.form_submit_button("Añadir") and proy.strip() and tarea.strip():
            add(
                "proyectos",
                {"proyecto": proy, "tarea": tarea, "estado": estado, "prioridad": pr},
            )
            st.rerun()
    df = cargar("proyectos")
    if df.empty:
        st.info("No hay proyectos.")
    else:
        for p in df["proyecto"].unique():
            st.markdown(f"### {p}")
            st.dataframe(df[df["proyecto"] == p], use_container_width=True)


def seccion_universidad():
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


def seccion_viajes():
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


def seccion_notas():
    with st.form("form_nota"):
        titulo = st.text_input("Título")
        cat = st.selectbox(
            "Categoría",
            ["Idea", "Recordatorio", "Universidad", "Proyecto", "Personal", "Otro"],
        )
        vinculo = st.text_input(
            "Vincular a proyecto/tema", placeholder="Ej: RUNATICS, Erasmus, Universidad"
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
                st.caption(f"{r['categoria']} | Vinculo: {r.get('vinculo', '')}")
                st.write(r["nota"])


with tabs[7]:
    st.subheader("💳 Suscripciones")
    seccion_suscripciones()
with tabs[8]:
    st.subheader("⭐ Wishlist")
    seccion_wishlist()
with tabs[9]:
    st.subheader("🛒 Compras")
    seccion_compras()
with tabs[10]:
    st.subheader("🎯 Objetivos")
    seccion_objetivos()
with tabs[11]:
    st.subheader("📚 Proyectos")
    seccion_proyectos()
with tabs[12]:
    st.subheader("🎓 Universidad")
    seccion_universidad()
with tabs[13]:
    st.subheader("✈️ Viajes")
    seccion_viajes()
with tabs[14]:
    st.subheader("📝 Notas")
    seccion_notas()

with tabs[15]:
    st.subheader("📂 Archivos adjuntos")
    st.warning(
        "Los metadatos se sincronizan en Supabase. El archivo físico se guarda localmente en este PC. Para nube completa de archivos habrá que activar Supabase Storage."
    )
    with st.form("form_archivo"):
        archivo = st.file_uploader("Subir archivo")
        categoria = st.selectbox(
            "Categoría",
            ["Universidad", "Viaje", "Proyecto", "Personal", "Finanzas", "Otro"],
        )
        vinculo = st.text_input(
            "Vincular a proyecto/tema", placeholder="Ej: Erasmus, RUNATICS, Empresa"
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
            st.success("Archivo guardado.")
            st.rerun()
    tabla_simple("archivos")

with tabs[16]:
    st.subheader("🧠 Segundo cerebro")
    proyectos, notas, archivos, viajes, uni = (
        cargar("proyectos"),
        cargar("notas"),
        cargar("archivos"),
        cargar("viajes"),
        cargar("universidad"),
    )
    temas = set()
    for df_, col in [
        (proyectos, "proyecto"),
        (notas, "vinculo"),
        (archivos, "vinculo"),
        (viajes, "viaje"),
        (uni, "asignatura"),
    ]:
        if not df_.empty and col in df_.columns:
            temas.update([str(x) for x in df_[col].dropna().unique() if str(x).strip()])
    if not temas:
        st.info(
            "Todavía no hay temas vinculados. Usa el campo 'vincular' en notas o archivos."
        )
    else:
        tema = st.selectbox("Tema/proyecto", sorted(temas))
        st.markdown(f"## {tema}")
        st.subheader("Notas relacionadas")
        st.dataframe(
            (
                notas[notas["vinculo"].astype(str).str.lower() == tema.lower()]
                if not notas.empty
                else pd.DataFrame()
            ),
            use_container_width=True,
        )
        st.subheader("Archivos relacionados")
        st.dataframe(
            (
                archivos[archivos["vinculo"].astype(str).str.lower() == tema.lower()]
                if not archivos.empty
                else pd.DataFrame()
            ),
            use_container_width=True,
        )
        st.subheader("Tareas/proyectos relacionados")
        st.dataframe(
            (
                proyectos[proyectos["proyecto"].astype(str).str.lower() == tema.lower()]
                if not proyectos.empty
                else pd.DataFrame()
            ),
            use_container_width=True,
        )

with tabs[17]:
    st.subheader("📊 Estadísticas")
    tareas, finanzas, objetivos, log = (
        cargar("tareas"),
        cargar("finanzas"),
        cargar("objetivos"),
        cargar("habitos_log"),
    )
    xp, nivel, resto = calcular_nivel()
    c1, c2, c3 = st.columns(3)
    c1.metric("Nivel", nivel)
    c2.metric("XP total", xp)
    c3.metric("Productividad 7 días", f"{productividad_score()}%")
    if not tareas.empty:
        comp = tareas["completada"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Tareas completadas", int(comp))
        c2.metric("Tareas totales", len(tareas))
        c3.metric("Ratio", f"{comp/len(tareas)*100:.1f}%")
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

with tabs[18]:
    st.subheader("☁️ Copias y sincronización")
    st.success("Datos principales sincronizados en Supabase.")
    st.download_button(
        "Descargar copia ZIP local del usuario actual",
        data=exportar_zip_usuario(),
        file_name=f"life_os_backup_{usuario_actual}.zip",
        mime="application/zip",
    )
    st.caption("El ZIP es solo copia local. Los datos principales están en Supabase.")

with tabs[19]:
    st.subheader("🤖 Asistente IA")
    pregunta = st.text_area(
        "Pregunta", placeholder="Ej: ¿Qué debería priorizar esta semana?"
    )
    if st.button("Preguntar") and pregunta.strip():
        with st.spinner("Analizando tus datos..."):
            st.markdown(preguntar_ia(pregunta))
