import io
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def export_heatmap_to_pdf(data, filtered_data, heatmap_fig, pie_fig, bar_fig, 
                          selected_estate, critical_count, under_count, optimal_count,
                          critical_data, under_data, optimal_data, total_loss):
    """
    Export heatmap summary data to PDF
    """
    
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Create PDF document with landscape orientation
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                            rightMargin=0.5*cm, leftMargin=0.5*cm,
                            topMargin=1*cm, bottomMargin=0.5*cm)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=15,
        textColor=colors.HexColor('#2c3e50')
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        alignment=TA_LEFT,
        spaceAfter=8,
        textColor=colors.HexColor('#34495e')
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        spaceAfter=4
    )
    
    # Story elements list
    story = []
    
    # =============================
    # TITLE
    # =============================
    title = Paragraph("Productivity Heatmap Report", title_style)
    story.append(title)
    
    # Filter info
    filter_text = f"Estate: {selected_estate} | Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}"
    filter_para = Paragraph(filter_text, normal_style)
    story.append(filter_para)
    story.append(Spacer(1, 10))
    
    # =============================
    # SUMMARY STATISTICS TABLE
    # =============================
    story.append(Paragraph("Summary Statistics", heading_style))
    
    summary_data = [
        ['Total Blocks', 'Total Area (Ha)', 'Avg Productivity', 'Max Productivity', 'Min Productivity'],
        [
            f"{len(filtered_data):,}",
            f"{filtered_data['luas_ha'].sum():,.2f}",
            f"{filtered_data['produktivitas'].mean():.2f}",
            f"{filtered_data['produktivitas'].max():.2f}",
            f"{filtered_data['produktivitas'].min():.2f}"
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[2.2*cm, 2.5*cm, 2.5*cm, 2.2*cm, 2.2*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # =============================
    # STATUS DISTRIBUTION TABLE
    # =============================
    story.append(Paragraph("Status Distribution", heading_style))
    
    status_counts = filtered_data['status'].value_counts()
    total = len(filtered_data)
    
    status_data = [
        ['Status', 'Count', 'Percentage'],
        ['Critical', str(status_counts.get('Critical', 0)), f"{status_counts.get('Critical', 0)/total*100:.1f}%" if total > 0 else "0%"],
        ['Underperform', str(status_counts.get('Underperform', 0)), f"{status_counts.get('Underperform', 0)/total*100:.1f}%" if total > 0 else "0%"],
        ['Optimal', str(status_counts.get('Optimal', 0)), f"{status_counts.get('Optimal', 0)/total*100:.1f}%" if total > 0 else "0%"]
    ]
    
    status_table = Table(status_data, colWidths=[4*cm, 3*cm, 4*cm])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 15))
    
    # =============================
    # CRITICAL BLOCKS
    # =============================
    if critical_count > 0 and critical_data is not None and len(critical_data) > 0:
        story.append(Paragraph(f"Critical Blocks ({critical_count} blocks)", heading_style))
        
        critical_display = critical_data[['estate', 'afdeling', 'blok', 'luas_ha', 'produktivitas']].copy()
        critical_display['produktivitas'] = critical_display['produktivitas'].round(2)
        critical_display.columns = ['Estate', 'Afdeling', 'Blok', 'Luas (Ha)', 'Produktivitas']
        
        # Convert to list for table
        critical_list = [critical_display.columns.tolist()] + critical_display.head(20).values.tolist()
        
        col_widths = [2.5*cm, 2.5*cm, 1.8*cm, 2*cm, 2*cm]
        critical_table = Table(critical_list, colWidths=col_widths, repeatRows=1)
        critical_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff5f5')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(critical_table)
        story.append(Spacer(1, 10))
    
    # =============================
    # UNDERPERFORM BLOCKS
    # =============================
    if under_count > 0 and under_data is not None and len(under_data) > 0:
        story.append(Paragraph(f"Underperform Blocks ({under_count} blocks)", heading_style))
        
        under_display = under_data[['estate', 'afdeling', 'blok', 'luas_ha', 'produktivitas']].copy()
        under_display['produktivitas'] = under_display['produktivitas'].round(2)
        under_display.columns = ['Estate', 'Afdeling', 'Blok', 'Luas (Ha)', 'Produktivitas']
        
        under_list = [under_display.columns.tolist()] + under_display.head(20).values.tolist()
        
        under_table = Table(under_list, colWidths=col_widths, repeatRows=1)
        under_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1c40f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fffbea')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(under_table)
        story.append(Spacer(1, 10))
    
    # =============================
    # OPTIMAL BLOCKS
    # =============================
    if optimal_count > 0 and optimal_data is not None and len(optimal_data) > 0:
        story.append(Paragraph(f"Optimal Blocks ({optimal_count} blocks)", heading_style))
        
        optimal_display = optimal_data[['estate', 'afdeling', 'blok', 'luas_ha', 'produktivitas']].copy()
        optimal_display['produktivitas'] = optimal_display['produktivitas'].round(2)
        optimal_display.columns = ['Estate', 'Afdeling', 'Blok', 'Luas (Ha)', 'Produktivitas']
        
        optimal_list = [optimal_display.columns.tolist()] + optimal_display.head(20).values.tolist()
        
        optimal_table = Table(optimal_list, colWidths=col_widths, repeatRows=1)
        optimal_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3fff5')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        story.append(optimal_table)
        story.append(Spacer(1, 10))
    
    # =============================
    # TOP 10 RANKINGS
    # =============================
    story.append(Paragraph("Top 10 Rankings", heading_style))
    
    # Worst 10
    worst_blocks = filtered_data.nsmallest(10, 'produktivitas')[['blok', 'estate', 'afdeling', 'produktivitas']]
    worst_blocks['produktivitas'] = worst_blocks['produktivitas'].round(2)
    
    worst_data = [['Blok', 'Estate', 'Afdeling', 'Produktivitas']] + worst_blocks.values.tolist()
    worst_table = Table(worst_data, colWidths=[2.5*cm, 3*cm, 3*cm, 2.5*cm])
    worst_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff5f5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    # Best 10
    best_blocks = filtered_data.nlargest(10, 'produktivitas')[['blok', 'estate', 'afdeling', 'produktivitas']]
    best_blocks['produktivitas'] = best_blocks['produktivitas'].round(2)
    
    best_data = [['Blok', 'Estate', 'Afdeling', 'Produktivitas']] + best_blocks.values.tolist()
    best_table = Table(best_data, colWidths=[2.5*cm, 3*cm, 3*cm, 2.5*cm])
    best_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3fff5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    # Two column layout for rankings
    ranking_data = [[worst_table, best_table]]
    ranking_layout = Table(ranking_data, colWidths=[13*cm, 13*cm])
    story.append(ranking_layout)
    story.append(Spacer(1, 15))
    
    # =============================
    # LOSS INFORMATION
    # =============================
    if total_loss > 0:
        story.append(Paragraph("Production Loss Analysis", heading_style))
        loss_para = Paragraph(f"Estimated Production Loss from 25 Ton/Ha target: <b>{total_loss:,.1f} Ton</b>", normal_style)
        story.append(loss_para)
        story.append(Spacer(1, 15))
    
    # =============================
    # FOOTER
    # =============================
    footer_text = f"Report generated by Palm Plantation Analytics System | {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
    footer = Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey))
    story.append(footer)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer


def export_full_report_to_pdf(data, filtered_data, heatmap_fig, pie_fig, bar_fig, 
                               selected_estate, critical_count, under_count, optimal_count,
                               critical_data, under_data, optimal_data, total_loss):
    """
    Export complete report including charts to PDF
    """
    # Untuk sementara, gunakan fungsi yang sama dengan export_heatmap_to_pdf
    # Karena plotly figures memerlukan konfigurasi khusus untuk export ke PDF
    return export_heatmap_to_pdf(data, filtered_data, heatmap_fig, pie_fig, bar_fig, 
                                  selected_estate, critical_count, under_count, optimal_count,
                                  critical_data, under_data, optimal_data, total_loss)