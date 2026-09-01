import pandas as pd
import streamlit as st
import yfinance as yf

# Configuración visual de la página
st.set_page_config(
    page_title="Agente de Trading - CEDEARs", page_icon="📈", layout="centered"
)

st.title("🤖 Mi Agente de Trading - CEDEARs")
st.write(
    "Ingresa el ticker del CEDEAR o acción que deseas analizar (ej: AAPL, MELI,"
    " KO, TSLA):"
)

# Campo de entrada de usuario (UI)
ticker_input = st.text_input("Ticker de la empresa:", value="AAPL").upper()

if st.button("Analizar Activo"):
  with st.spinner(f"Analizando {ticker_input} en tiempo real..."):
    try:
      # Descargamos los datos
      datos = yf.download(ticker_input, period="6mo", progress=False)

      if datos.empty:
        st.error(
            "No se encontraron datos para ese ticker. Verifica que esté bien"
            " escrito."
        )
      else:
        # Aplanamos columnas si viene en MultiIndex
        if isinstance(datos.columns, pd.MultiIndex):
          datos.columns = datos.columns.get_level_values(0)

        # 1. Indicadores Técnicos
        datos["Media_20"] = datos["Close"].rolling(window=20).mean()
        datos["Media_50"] = datos["Close"].rolling(window=50).mean()

        delta = datos["Close"].diff()
        ganancia = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        perdida = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = ganancia / perdida
        datos["RSI"] = 100 - (100 / (1 + rs))

        exp12 = datos["Close"].ewm(span=12, adjust=False).mean()
        exp26 = datos["Close"].ewm(span=26, adjust=False).mean()
        datos["MACD"] = exp12 - exp26
        datos["Signal_Line"] = datos["MACD"].ewm(span=9, adjust=False).mean()

        # Valores actuales
        precio_actual = float(datos["Close"].iloc[-1])
        m20 = float(datos["Media_20"].iloc[-1])
        m50 = float(datos["Media_50"].iloc[-1])
        rsi_actual = float(datos["RSI"].iloc[-1])
        macd_val = float(datos["MACD"].iloc[-1])
        signal_val = float(datos["Signal_Line"].iloc[-1])

        # Lógica de decisión
        if m20 > m50 and macd_val > signal_val and rsi_actual < 70:
          senal = "🟢 COMPRA FUERTE (Alcista)"
        elif m20 > m50:
          senal = "🟡 MANTENER / PRECAUCIÓN (RSI Alto)"
        elif m20 < m50 and macd_val > signal_val:
          senal = "🔵 POSIBLE REBOTE"
        else:
          senal = "🔴 VENTA / BAJISTA"

        # Mostramos los resultados en la interfaz
        st.success(f"Análisis completado para: {ticker_input}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Precio Actual", f"${precio_actual:,.2f}")
        col2.metric("RSI (14)", f"{rsi_actual:.1f}")
        col3.metric("Señal del Agente", senal)

        # Gráfico de evolución de precios y medias móviles
        st.subheader("Evolución de Precios y Medias Móviles")
        st.line_chart(datos[["Close", "Media_20", "Media_50"]])

    except Exception as e:
      st.error(f"Ocurrió un error al procesar el activo: {e}")