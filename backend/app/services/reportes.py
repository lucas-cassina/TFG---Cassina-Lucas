"""
Generación de reportes PDF individuales para auditores (CIAS-005 / HU-010).
Usa ReportLab.
"""

import io
from datetime import datetime
from xml.sax.saxutils import escape
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
        ["N° Póliza", datos.get("numero_poliza") or "Sin póliza cargada"],
        ["Vehículo", f"{datos.get('marca_vehiculo') or '—'} {datos.get('modelo_vehiculo') or ''} ({datos.get('anio_vehiculo') or '—'})"],
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
        ["Promedio últimos 180 días", f"{datos.get('indice_promedio_6m', 'N/D')}"],
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

    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Período analizado", style_h2))
    story.append(Paragraph(
        f"Desde {datos.get('periodo_desde', 'N/D')} hasta {datos.get('periodo_hasta', 'N/D')}. "
        "El promedio resume los últimos 180 días; el desglose corresponde al índice más reciente.",
        style_normal))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph("Desglose del índice actual", style_h2))
    filas = [["Variable", "Puntaje / 100", "Peso", "Contribución"]]
    variables = [("Velocidad", "puntaje_velocidad", .25),
                 ("Frenadas", "puntaje_frenadas", .25),
                 ("Aceleraciones", "puntaje_aceleraciones", .20),
                 ("Horario", "puntaje_horario", .15),
                 ("Distancia", "puntaje_distancia", .15)]
    for nombre, clave, peso in variables:
        valor = datos.get("desglose", {}).get(clave)
        filas.append([nombre, f"{valor:.2f}" if valor is not None else "N/D",
                      f"{peso:.0%}", f"{valor * peso:.2f}" if valor is not None else "N/D"])
    tabla = Table(filas, colWidths=[5*cm, 4*cm, 3*cm, 5*cm], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c5e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tabla)
    story.append(Spacer(1, .4*cm))
    story.append(Paragraph("Alertas del período", style_h2))
    alertas = datos.get("alertas", [])
    if not alertas:
        story.append(Paragraph("No hay alertas registradas en el período.", style_normal))
    else:
        filas = [["Fecha UTC", "Evento", "Descripción"]]
        for alerta in alertas:
            filas.append([
                alerta["fecha"],
                Paragraph(escape(alerta["tipo"].replace("_", " ")), style_normal),
                Paragraph(escape(alerta["descripcion"]), style_normal),
            ])
        tabla = Table(filas, colWidths=[3.5*cm, 4.5*cm, 9*cm], repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c5e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), .5, colors.HexColor("#cccccc")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tabla)

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


def generar_poliza_pdf(datos: dict) -> bytes:
    """
    Genera el documento PDF de la póliza del asegurado.

    Claves esperadas en datos: nombre, apellido, dni, email, telefono,
    fecha_nacimiento, numero_poliza, marca_vehiculo, modelo_vehiculo,
    anio_vehiculo, patente, zona, fecha_inicio, fecha_vencimiento.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "pt", parent=styles["Title"],
        fontSize=20, spaceAfter=4, alignment=TA_CENTER,
        textColor=colors.HexColor("#1a3c5e"),
    )
    style_subtitle = ParagraphStyle(
        "ps", parent=styles["Normal"],
        fontSize=11, spaceAfter=2, alignment=TA_CENTER,
        textColor=colors.HexColor("#4a6fa5"),
    )
    style_h2 = ParagraphStyle(
        "ph2", parent=styles["Heading2"],
        fontSize=12, spaceBefore=14, spaceAfter=5,
        textColor=colors.HexColor("#1a3c5e"),
    )
    style_small = ParagraphStyle(
        "psmall", parent=styles["Normal"],
        fontSize=8, textColor=colors.grey, alignment=TA_CENTER,
    )

    tbl_style = TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf0f6")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])

    story = []

    # Encabezado
    story.append(Paragraph("CIAS — Ciudadano Asegurado", style_title))
    story.append(Paragraph("Póliza de Seguro Automotor", style_subtitle))
    story.append(Paragraph(
        f"Emitida el {datetime.now().strftime('%d/%m/%Y')}  ·  N° {datos.get('numero_poliza', '-')}",
        style_subtitle,
    ))
    story.append(Spacer(1, 0.6*cm))

    # Banda de estado vigente/vencida
    vigente = True
    try:
        from datetime import date
        fv = datos.get("fecha_vencimiento")
        if fv:
            fv_date = date.fromisoformat(str(fv))
            vigente = fv_date >= date.today()
    except Exception:
        pass

    estado_color = colors.HexColor("#27ae60") if vigente else colors.HexColor("#e74c3c")
    estado_texto = "VIGENTE" if vigente else "VENCIDA"
    banda = Table([[f"Estado de la póliza: {estado_texto}"]], colWidths=[17*cm])
    banda.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), estado_color),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(banda)
    story.append(Spacer(1, 0.5*cm))

    # Datos del asegurado
    story.append(Paragraph("Datos del Asegurado", style_h2))
    t_asegurado = Table([
        ["Nombre completo", f"{datos.get('nombre', '')} {datos.get('apellido', '')}"],
        ["DNI", datos.get("dni", "-")],
        ["Correo electrónico", datos.get("email", "-")],
        ["Teléfono", datos.get("telefono") or "-"],
        ["Fecha de nacimiento", str(datos.get("fecha_nacimiento") or "-")],
    ], colWidths=[5*cm, 12*cm])
    t_asegurado.setStyle(tbl_style)
    story.append(t_asegurado)

    # Datos del vehículo
    story.append(Paragraph("Vehículo Asegurado", style_h2))
    t_vehiculo = Table([
        ["Marca / Modelo", f"{datos.get('marca_vehiculo', '-')} {datos.get('modelo_vehiculo', '')}"],
        ["Año", str(datos.get("anio_vehiculo", "-"))],
        ["Patente", datos.get("patente", "-")],
        ["Zona de operación", datos.get("zona") or "-"],
    ], colWidths=[5*cm, 12*cm])
    t_vehiculo.setStyle(tbl_style)
    story.append(t_vehiculo)

    # Vigencia
    story.append(Paragraph("Vigencia", style_h2))
    t_vigencia = Table([
        ["N° de póliza", datos.get("numero_poliza") or "Sin póliza cargada"],
        ["Inicio de cobertura", str(datos.get("fecha_inicio", "-"))],
        ["Vencimiento", str(datos.get("fecha_vencimiento", "-"))],
    ], colWidths=[5*cm, 12*cm])
    t_vigencia.setStyle(tbl_style)
    story.append(t_vigencia)

    # Coberturas
    story.append(Paragraph("Coberturas Incluidas", style_h2))
    coberturas = [
        ["✓", "Responsabilidad Civil Obligatoria (RCO)"],
        ["✓", "Daños parciales por choque o vuelco"],
        ["✓", "Robo o hurto total del vehículo"],
        ["✓", "Incendio total o parcial"],
        ["✓", "Granizo y fenómenos de la naturaleza"],
        ["✓", "Asistencia al viajero 24 hs"],
        ["◆", "Bonificación telemétrica según índice de riesgo CIAS"],
    ]
    t_coberturas = Table(coberturas, colWidths=[1*cm, 16*cm])
    t_coberturas.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f8fb")]),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, -1), (0, -1), colors.HexColor("#4a6fa5")),
    ]))
    story.append(t_coberturas)

    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph(
        "Este documento es el comprobante oficial de cobertura emitido por CIAS. "
        "Para consultas: soporte@cias.ar  ·  SSN Argentina",
        style_small,
    ))

    doc.build(story)
    return buffer.getvalue()
