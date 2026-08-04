from django.template.loader import get_template
from xhtml2pdf import pisa
import io

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return result  # This is a BytesIO object
    return None

def generate_pdf_receipt(order):
    total = sum(item.quantity * item.price for item in order.items.all())
    context = {
        'order': order,
        'total': total
    }
    return render_to_pdf('receipts/pdffile.html', context)

import ipfshttpclient

def upload_pdf_to_ipfs(pdf_file):
    # Connect to your local IPFS node (make sure IPFS Desktop or daemon is running)
    client = ipfshttpclient.connect()  # defaults to /dns/localhost/tcp/5001/http

    # Upload PDF
    result = client.add(pdf_file)

    # Return the IPFS hash
    return result['Hash']

