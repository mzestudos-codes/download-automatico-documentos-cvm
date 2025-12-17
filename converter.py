import re, json, os, html

def converter_html_para_json(arquivo_html, arquivo_json):
    if not os.path.exists(arquivo_html): return
    with open(arquivo_html, 'r', encoding='utf-8') as f:
        html_bruto = f.read()

    conteudos = re.findall(r'value="([^"]+)"', html_bruto)
    texto_total = html.unescape(" ".join(conteudos))
    matches = re.findall(r'value="([^"]+)"[^>]*>([^<]+)', texto_total)

    banco_dados = []
    for valor, texto in matches:
        if valor == "-1": continue
        partes = [p.strip() for p in texto.split('|') if p.strip()]
        cat = partes[0] if len(partes) > 0 else ""
        tipo = partes[1] if len(partes) > 1 else "TODOS"
        esp = partes[2] if len(partes) > 2 else "TODAS"
        banco_dados.append({"id": valor, "categoria": cat, "tipo": tipo, "especie": esp})

    with open(arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(banco_dados, f, indent=4, ensure_ascii=False)
    print(f"✅ JSON estruturado gerado!")

if __name__ == "__main__":
    converter_html_para_json("categorias.html", "categorias.json")