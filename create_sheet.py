import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

def create_and_share_sheet():
    # Configurar as credenciais
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(credentials)
    
    # Criar uma nova planilha
    sheet_name = "Currículos - Análise IA"
    try:
        sheet = client.create(sheet_name)
        print(f"Planilha '{sheet_name}' criada com sucesso!")
    except Exception as e:
        print(f"Erro ao criar planilha: {e}")
        return
    
    # Configurar as colunas da planilha
    worksheet = sheet.get_worksheet(0)
    
    # Cabeçalhos da planilha
    headers = [
        "Nome do Candidato",
        "Email",
        "Telefone",
        "Cargo Desejado",
        "Experiência (anos)",
        "Formação",
        "Idiomas",
        "Habilidades Principais",
        "Link do Currículo",
        "ID do Arquivo",
        "Status da Análise",
        "Pontuação Final",
        "Data de Inclusão"
    ]
    
    # Inserir cabeçalhos
    worksheet.update('A1:M1', [headers])
    
    # Formatar cabeçalhos (negrito)
    worksheet.format('A1:M1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
    })
    
    # Ajustar largura das colunas
    column_widths = [20, 25, 15, 20, 15, 20, 15, 30, 40, 30, 15, 15, 15]
    for i, width in enumerate(column_widths):
        worksheet.set_column_width(i + 1, width)
    
    # Compartilhar a planilha
    try:
        sheet.share('matheusbnas@gmail.com', perm_type='user', role='writer')
        print(f"Planilha compartilhada com matheusbnas@gmail.com")
    except Exception as e:
        print(f"Erro ao compartilhar planilha: {e}")
    
    # Mostrar informações da planilha
    print(f"\n=== INFORMAÇÕES DA PLANILHA ===")
    print(f"Nome: {sheet_name}")
    print(f"URL: {sheet.url}")
    print(f"ID: {sheet.id}")
    print(f"Compartilhada com: matheusbnas@gmail.com")
    print(f"\nUse o nome '{sheet_name}' no sistema de análise de currículos!")
    
    return sheet

if __name__ == "__main__":
    create_and_share_sheet() 