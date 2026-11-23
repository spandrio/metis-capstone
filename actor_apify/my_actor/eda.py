"""EDA: resumen del mercado que responde las preguntas de negocio de la presentación."""
import pandas as pd


def resumen_eda(df: pd.DataFrame) -> dict:
    """EDA encapsulado: las preguntas de negocio que responde la presentación."""
    return {
        "total_productos_limpios": int(len(df)),
        "precio_promedio_por_marca": df.groupby("marca")["precio"].mean().round(2).to_dict(),
        "publicaciones_por_categoria": df["categoria"].value_counts().to_dict(),
        "precio_y_rating_promedio_por_categoria": df.groupby("categoria")[["precio", "rating"]].mean().round(2).to_dict(),
    }
