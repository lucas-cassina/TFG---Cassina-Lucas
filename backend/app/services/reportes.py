"""
Generación de reportes PDF individuales para auditores (CIAS-005 / HU-010).
Usa ReportLab.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generar_reporte_pdf(datos: dict) -> bytes:
    """
    Genera un reporte PDF de perfil de riesgo para un asegurado.

    Args:
        datos: dict con la información del conductor y su historial de riesgo.
               Claves esperadas: nombre, apellido, dni, email, numero_poliza,
               marca_vehiculo, modelo_vehiculo, anio_vehiculo, indice_actual,
               nivel_actual, indice_promedio_6m, total_sesiones, total_km,
               nivel_incentivo, historial (lista de dicts con fecha, indice, nivel)

    Returns:
        bytes del PDF generado.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "title", parent=styles["Title"],
        fontSize=18, spaceAfter=6, alignment=TA_CENTER,
        textColor=colors.HexColor("#1a3c5e")
    )
    style_h2 = ParagraphStyle(
        "h2", parent=styles["Heading2"],
        fontSize=13, spaceBefore=12, spaceAfter=4,
        textColor=colors.HexColor("#1a3c5e")
    )
    style_normal = styles["Normal"]

    nivel_colores = {
        "Bajo": colors.HexColor("#27ae60"),
        "Medio": colors.HexColor("#f39c12"),
        "Alto": colors.HexColor("#e74c3c"),
    }

    story = []

    # Encabezado
    story.append(Paragraph("CIAS — Ciudadano Asegurado", style_title))
    story.append(Paragraph("Reporte de Perfil de Riesgo Asegurador", style_title))
    story.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle("sub", parent=style_normal, alignment=TA_CENTER, textColor=colors.grey)
    ))
    story.append(Spacer(1, 0.5*cm))

    # Datos del asegurado
    story.append(Paragraph("Datos del Asegurado", style_h2))
    datos_tabla = [
        ["Nombre completo", f"{datos.get('nombre', '')} {datos.get('apellido', '')}"],
        ["DNI", datos.get("dni", "-")],
        ["Email", datos.get("email", "-")],
        ["N° Póliza", datos.get("numero_poliza", "-")],
        ["Vehículo", f"{datos.get('marca_vehiculo', '')} {datos.get('modelo_vehiculo', '')} ({datos.get('anio_vehiculo', '')})"],
    ]
    t = Table(datos_tabla, colWidths=[5*cm, 12*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf0f6")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # Índice de riesgo actual
    story.append(Paragraph("Índice de Riesgo", style_h2))
    nivel = datos.get("nivel_actual", "Sin datos")
    color_nivel = nivel_colores.get(nivel, colors.grey)
    indice_tabla = [
        ["Índice actual", f"{datos.get('indice_actual', 'N/D')}"],
        ["Nivel actual", nivel],
        ["Promedio últimos 6 meses", f"{datos.get('indice_promedio_6m', 'N/D')}"],
        ["Total sesiones", str(datos.get("total_sesiones", 0))],
        ["Kilómetros totales", f"{datos.get('total_km', 0):.1f} km"],
    ]
    t2 = Table(indice_tabla, colWidths=[5*cm, 12*cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf0f6")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (1, 1), (1, 1), color_nivel),
        ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.4*cm))

    # Nivel de incentivos
    story.append(Paragraph("Nivel de Incentivos", style_h2))
    story.append(Paragraph(
        f"Nivel alcanzado: <b>{datos.get('nivel_incentivo', 'Sin nivel')}</b>",
        style_normal
    ))
    story.append(Spacer(1, 0.4*cm))

    # Historial de sesiones
    historial = datos.get("historial", [])
    if historial:
        story.append(Paragraph("Historial de Sesiones (últimas 10)", style_h2))
        encabezado = [["Fecha", "Índice", "Nivel", "Distancia (km)"]]
        filas = []
        for s in historial[-10:]:
            filas.append([
                s.get("fecha", "-"),
                str(s.get("indice", "-")),
                s.get("nivel", "-"),
                f"{s.get('distancia_km', 0):.1f}",
            ])
        tabla_hist = Table(encabezado + filas, colWidths=[4*cm, 3*cm, 3*cm, 7*cm])
        tabla_hist.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c5e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fb")]),
        ]))
        story.append(tabla_hist)

    # Nota final
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph(
        "Este reporte fue generado automáticamente por el sistema CIAS. "
        "Los datos reflejan la información disponible al momento de la generación.",
        ParagraphStyle("footer", parent=style_normal, fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    return buffer.getvalue()
