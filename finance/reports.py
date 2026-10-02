import csv
from io import BytesIO
from django.http import HttpResponse
from decimal import Decimal
from .services import format_currency

def export_transactions_csv(report_data):
    """
    Generates downloadable CSV report file for the given transactions & summary.
    """
    response = HttpResponse(content_type='text/csv')
    period_str = f"{report_data['start_date']} to {report_data['end_date']}"
    filename = f"finance_report_{report_data['period']}_{report_data['start_date']}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['PERSONAL FINANCE REPORT'])
    writer.writerow(['Period', period_str])
    writer.writerow([])
    writer.writerow(['SUMMARY METRICS'])
    writer.writerow(['Total Income', float(report_data['income_total'])])
    writer.writerow(['Total Expenses', float(report_data['expense_total'])])
    writer.writerow(['Net Balance', float(report_data['net_balance'])])
    writer.writerow(['Total Transactions', report_data['total_count']])
    writer.writerow(['Largest Expense', float(report_data['largest_expense'])])
    writer.writerow(['Top Category', report_data['top_category_name']])
    writer.writerow([])
    writer.writerow(['TRANSACTIONS'])
    writer.writerow(['ID', 'Date', 'Type', 'Category', 'Description', 'Payment Method', 'Amount', 'Notes'])

    for tx in report_data['transactions']:
        cat_name = tx.category.name if tx.category else 'Uncategorized'
        writer.writerow([
            tx.id,
            tx.transaction_date.strftime('%Y-%m-%d'),
            tx.transaction_type,
            cat_name,
            tx.description,
            tx.get_payment_method_display(),
            float(tx.amount),
            tx.notes
        ])

    return response


def export_transactions_pdf(report_data):
    """
    Generates a clean PDF document using ReportLab.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        # Fallback if ReportLab is unavailable
        response = HttpResponse("ReportLab library not installed on server.", content_type="text/plain")
        return response

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1E1B4B'),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15,
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#334155'),
        spaceBefore=12,
        spaceAfter=8,
    )
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1E293B'),
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("Personal Finance Statement", title_style))
    period_text = f"Report Period: <b>{report_data['start_date'].strftime('%d %b %Y')}</b> to <b>{report_data['end_date'].strftime('%d %b %Y')}</b>"
    elements.append(Paragraph(period_text, subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=15))

    # KPI Summary Table
    elements.append(Paragraph("Financial Summary", section_heading))
    kpi_data = [
        [
            Paragraph("<b>Total Income</b>", cell_style),
            Paragraph(f"<font color='#059669'><b>{report_data['formatted_income']}</b></font>", cell_style),
            Paragraph("<b>Total Expenses</b>", cell_style),
            Paragraph(f"<font color='#DC2626'><b>{report_data['formatted_expense']}</b></font>", cell_style),
        ],
        [
            Paragraph("<b>Net Balance</b>", cell_style),
            Paragraph(f"<b>{report_data['formatted_net']}</b>", cell_style),
            Paragraph("<b>Total Transactions</b>", cell_style),
            Paragraph(f"<b>{report_data['total_count']}</b>", cell_style),
        ],
        [
            Paragraph("<b>Largest Expense</b>", cell_style),
            Paragraph(f"<b>{report_data['formatted_largest']}</b>", cell_style),
            Paragraph("<b>Top Category</b>", cell_style),
            Paragraph(f"<b>{report_data['top_category_name']}</b>", cell_style),
        ]
    ]

    kpi_table = Table(kpi_data, colWidths=[130, 140, 130, 140])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 15))

    # Transactions Table
    elements.append(Paragraph("Transactions Detail", section_heading))

    tx_table_data = [
        [
            Paragraph("<b>Date</b>", cell_style),
            Paragraph("<b>Type</b>", cell_style),
            Paragraph("<b>Category</b>", cell_style),
            Paragraph("<b>Description</b>", cell_style),
            Paragraph("<b>Method</b>", cell_style),
            Paragraph("<b>Amount</b>", cell_style),
        ]
    ]

    for tx in report_data['transactions']:
        type_color = '#059669' if tx.transaction_type == 'INCOME' else '#DC2626'
        cat_name = f"{tx.category.icon} {tx.category.name}" if tx.category else "Uncategorized"
        amt_prefix = "+" if tx.transaction_type == 'INCOME' else "-"

        tx_table_data.append([
            Paragraph(tx.transaction_date.strftime('%d %b %Y'), cell_style),
            Paragraph(f"<font color='{type_color}'><b>{tx.get_transaction_type_display()}</b></font>", cell_style),
            Paragraph(cat_name, cell_style),
            Paragraph(tx.description or '-', cell_style),
            Paragraph(tx.get_payment_method_display(), cell_style),
            Paragraph(f"<font color='{type_color}'><b>{amt_prefix} {format_currency(tx.amount)}</b></font>", cell_style),
        ])

    if len(tx_table_data) == 1:
        tx_table_data.append([Paragraph("No transactions recorded for this period.", cell_style), "", "", "", "", ""])

    tx_table = Table(tx_table_data, colWidths=[75, 60, 110, 145, 65, 85])
    tx_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4F46E5')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))

    # Modify header style in table data
    for col_idx in range(6):
        tx_table_data[0][col_idx].style.textColor = colors.white

    elements.append(tx_table)

    # Build document
    doc.build(elements)
    pdf_value = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    filename = f"finance_report_{report_data['period']}_{report_data['start_date']}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf_value)
    return response
