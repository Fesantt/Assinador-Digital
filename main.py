import io
import json
import os
from tkinter import Tk, Canvas, filedialog, messagebox, Button, Radiobutton, IntVar
from PIL import Image, ImageTk
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import fitz
import PyPDF2
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
from Crypto.PublicKey import RSA
from Crypto.Util import asn1

def adicionar_logo_e_texto(pdf_in_path, pdf_out_path, logo_path, logo_pos, texto_pos, logo_angle, logo_orientation):
    pdf_leitura = PyPDF2.PdfReader(pdf_in_path)
    pdf_escrita = PyPDF2.PdfWriter()

    img_logo = ImageReader(logo_path)
    fonte_tamanho = 10

    for i in range(len(pdf_leitura.pages)):
        pagina = pdf_leitura.pages[i]

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        page_width = float(pagina.mediabox.width)
        page_height = float(pagina.mediabox.height)

        logo_x, logo_y = logo_pos
        logo_y = page_height - logo_y - 50 

        texto_x, texto_y = texto_pos
        texto_y = page_height - texto_y - 12

        can.saveState()
        can.translate(logo_x + 35, logo_y + 25)
        can.rotate(logo_angle)
        if logo_orientation == 2:
            can.rotate(90)
        can.drawImage(img_logo, -35, -25, width=70, height=50)
        can.restoreState()

        can.setFont("Helvetica", fonte_tamanho)
        can.drawString(texto_x, texto_y, "Assinado digitalmente")
        can.save()
        packet.seek(0)

        nova_pagina = PyPDF2.PdfReader(packet)
        pagina.merge_page(nova_pagina.pages[0])
        pdf_escrita.add_page(pagina)

    with open(pdf_out_path, 'wb') as arquivo_pdf_saida:
        pdf_escrita.write(arquivo_pdf_saida)

def assinar_pdf(pdf_path, certificado_path, senha):
    with open(certificado_path, "rb") as f:
        chave_privada = RSA.import_key(f.read(), passphrase=senha)
    
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
        hash_pdf = SHA256.new(pdf_data)
    
    assinatura = pkcs1_15.new(chave_privada).sign(hash_pdf)
    
    der = asn1.DerSequence([0, assinatura])
    
    return der.encode()

def selecionar_posicao_pdf(pdf_path, logo_path):
    global logo_pos, texto_pos, logo_offset_x, logo_offset_y, texto_offset_x, texto_offset_y, logo_angle
    global logo_orientation
    logo_pos = (50, 50)
    texto_pos = (50, 102)
    logo_offset_x, logo_offset_y = 0, 0
    texto_offset_x, texto_offset_y = 0, 0
    logo_angle = 0

    def iniciar_desenho_logo(event):
        global logo_offset_x, logo_offset_y
        logo_offset_x = event.x - logo_pos[0]
        logo_offset_y = event.y - logo_pos[1]

    def iniciar_desenho_texto(event):
        global texto_offset_x, texto_offset_y
        texto_offset_x = event.x - texto_pos[0]
        texto_offset_y = event.y - texto_pos[1]

    def arrastar_logo(event):
        global logo_pos
        logo_pos = (event.x - logo_offset_x, event.y - logo_offset_y)
        atualizar_preview()

    def arrastar_texto(event):
        global texto_pos
        texto_pos = (event.x - texto_offset_x, event.y - texto_offset_y)
        atualizar_preview()

    def rotacionar_logo(event):
        global logo_angle
        logo_angle += 5 if event.delta > 0 else -5
        atualizar_preview()

    def atualizar_preview():
        canvas.delete("preview")
        canvas.create_image(logo_pos[0], logo_pos[1], anchor='nw', image=logo_tk, tags="preview")
        canvas.create_text(texto_pos[0], texto_pos[1], text="Assinado digitalmente", anchor='nw', font=("Helvetica", 10), tags="preview")

    def salvar_layout():
        layout_data = {
            "logo_pos": logo_pos,
            "texto_pos": texto_pos,
            "logo_angle": logo_angle,
            "logo_orientation": logo_orientation.get()
        }
        with open("layout.json", "w") as file:
            json.dump(layout_data, file)
        messagebox.showinfo("Salvar Layout", "Layout salvo com sucesso.")

    def carregar_layout():
        try:
            with open("layout.json", "r") as file:
                layout_data = json.load(file)
            global logo_pos, texto_pos, logo_angle
            logo_pos = tuple(layout_data["logo_pos"])
            texto_pos = tuple(layout_data["texto_pos"])
            logo_angle = layout_data["logo_angle"]
            logo_orientation.set(layout_data["logo_orientation"])
            atualizar_preview()
            messagebox.showinfo("Carregar Layout", "Layout carregado com sucesso.")
        except FileNotFoundError:
            messagebox.showerror("Erro", "Nenhum layout salvo encontrado.")

    def assinar():
        adicionar_logo_e_texto(pdf_path, pdf_saida, logo_path, logo_pos, texto_pos, logo_angle, logo_orientation.get())
        
        assinatura = assinar_pdf(pdf_saida, certificado_path, senha_certificado)
        
        with open(pdf_saida, 'rb+') as f:
            pdf_data = f.read()
            f.seek(0)
            f.write(pdf_data + assinatura)

        messagebox.showinfo("Concluído", f"O PDF foi assinado e salvo em: {pdf_saida}")
        root.destroy()

    global root, img_tk, logo_tk, certificado_path, senha_certificado
    certificado_path = "certificado.pfx"
    senha_certificado = "1234567890"

    root = Tk()
    root.title("Seleção de Posição de Assinatura")

    doc = fitz.open(pdf_path)
    pagina = doc.load_page(0)
    pix = pagina.get_pixmap()
    img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_pil.thumbnail((600, 800), Image.LANCZOS)
    img_tk = ImageTk.PhotoImage(img_pil)

    canvas = Canvas(root, width=img_tk.width(), height=img_tk.height())
    canvas.pack()
    canvas.create_image(0, 0, anchor='nw', image=img_tk)

    logo_img = Image.open(logo_path)
    logo_img = logo_img.resize((70, 50), Image.LANCZOS)
    logo_tk = ImageTk.PhotoImage(logo_img)
    canvas.create_image(logo_pos[0], logo_pos[1], anchor='nw', image=logo_tk, tags="preview")
    canvas.create_text(texto_pos[0], texto_pos[1], text="Assinado digitalmente", anchor='nw', font=("Helvetica", 10), tags="preview")

    canvas.bind("<Button-1>", iniciar_desenho_logo)
    canvas.bind("<B1-Motion>", arrastar_logo)
    canvas.bind("<Button-3>", iniciar_desenho_texto)
    canvas.bind("<B3-Motion>", arrastar_texto)
    canvas.bind("<MouseWheel>", rotacionar_logo)

    logo_orientation = IntVar(value=1)
    Radiobutton(root, text="Horizontal", variable=logo_orientation, value=1).pack()
    Radiobutton(root, text="Vertical", variable=logo_orientation, value=2).pack()

    Button(root, text="Salvar Layout", command=salvar_layout).pack()
    Button(root, text="Carregar Layout", command=carregar_layout).pack()
    Button(root, text="Assinar", command=assinar).pack()

    root.mainloop()
    doc.close()

arquivo_pdf = filedialog.askopenfilename(title="Selecionar PDF", filetypes=[("PDF Files", "*.pdf")])
logo = filedialog.askopenfilename(title="Selecionar Logo", filetypes=[("Image Files", "*.jpg;*.png")])
pdf_saida = 'documento_assinado.pdf'

if arquivo_pdf and logo:
    selecionar_posicao_pdf(arquivo_pdf, logo)
