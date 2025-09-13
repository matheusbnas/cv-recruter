import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from typing import List, Dict, Any
import json
import io


class SheetCreator:
    def __init__(self):
        scope = ['https://www.googleapis.com/auth/spreadsheets',
                 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json', scope)
        self.client = gspread.authorize(credentials)

        # Criar cliente do Google Drive API
        self.drive_service = build('drive', 'v3', credentials=credentials)

    def create_job_sheet(self, job_name: str, share_email: str = "matheusbnas@gmail.com", use_existing: bool = False) -> Dict[str, Any]:
        """
        Cria uma nova planilha para uma vaga específica ou usa uma existente
        """
        try:
            # Criar planilha com nome baseado na vaga
            sheet_name = f"Currículos - {job_name}"

            # Se use_existing é True, tentar usar planilha existente primeiro
            if use_existing:
                try:
                    sheet = self.client.open(sheet_name)
                    print(f"✅ Planilha existente encontrada: {sheet_name}")
                except:
                    print(
                        f"⚠️ Planilha '{sheet_name}' não encontrada. Tentando criar nova...")
                    use_existing = False

            # Se não encontrou existente ou use_existing é False, tentar criar nova
            if not use_existing:
                try:
                    # Tentar criar planilha usando Google Drive API (na conta do usuário)
                    print(f"🔄 Tentando criar planilha na conta do usuário...")
                    return self.create_sheet_in_user_drive(job_name, share_email)

                except Exception as create_error:
                    print(
                        f"⚠️ Erro ao criar na conta do usuário: {create_error}")

                    # Fallback: tentar criar na Service Account
                    try:
                        sheet = self.client.create(sheet_name)
                        print(
                            f"✅ Nova planilha criada na Service Account: {sheet_name}")

                        # Compartilhar com a conta pessoal
                        try:
                            sheet.share(
                                share_email, perm_type='user', role='writer')
                            print(
                                f"✅ Planilha compartilhada com: {share_email}")
                        except Exception as share_error:
                            print(
                                f"⚠️ Erro ao compartilhar planilha: {share_error}")

                    except Exception as fallback_error:
                        if "quota has been exceeded" in str(fallback_error):
                            print(
                                f"⚠️ Cota do Google Drive excedida. Tentando usar planilha existente...")
                            # Tentar abrir planilha existente
                            try:
                                sheet = self.client.open(sheet_name)
                                print(
                                    f"✅ Planilha existente encontrada: {sheet_name}")
                            except:
                                print(
                                    f"❌ Não foi possível criar ou encontrar a planilha '{sheet_name}'")
                                print(f"💡 SOLUÇÕES:")
                                print(
                                    f"   1. Crie manualmente a planilha: {sheet_name}")
                                print(
                                    f"   2. Verifique se a Service Account tem permissão para sua conta")
                                print(
                                    f"   3. Use uma planilha existente com nome diferente")
                                # Retornar nome da planilha para que o usuário possa criar manualmente
                                return {
                                    'name': sheet_name,
                                    'url': f"https://docs.google.com/spreadsheets/create?title={sheet_name.replace(' ', '+')}",
                                    'id': None,
                                    'worksheet_id': None,
                                    'error': 'quota_exceeded'
                                }
                        else:
                            raise fallback_error

            # Configurar a planilha
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
                "Data de Inclusão",
                "Análise da IA"
            ]

            # Inserir cabeçalhos
            worksheet.update('A1:N1', [headers])

            # Formatar cabeçalhos
            worksheet.format('A1:N1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })

            # Ajustar largura das colunas
            column_widths = [20, 25, 15, 20, 15,
                             20, 15, 30, 40, 30, 15, 15, 15, 50]
            for i, width in enumerate(column_widths):
                worksheet.set_column_width(i + 1, width)

            # Congelar primeira linha
            worksheet.freeze(rows=1)

            # Compartilhar a planilha
            try:
                sheet.share(share_email, perm_type='user', role='writer')
                print(f"Planilha compartilhada com {share_email}")
            except Exception as e:
                print(f"Erro ao compartilhar planilha: {e}")

            return {
                'name': sheet_name,
                'url': sheet.url,
                'id': sheet.id,
                'worksheet_id': worksheet.id
            }

        except Exception as e:
            print(f"Erro ao criar planilha: {e}")
            raise e

    def create_sheet_in_user_drive(self, job_name: str, share_email: str = "matheusbnas@gmail.com") -> Dict[str, Any]:
        """
        Tenta criar uma planilha ou usar uma existente
        """
        try:
            sheet_name = f"Currículos - {job_name}"

            # Primeiro, tentar encontrar uma planilha existente
            try:
                sheet = self.client.open(sheet_name)
                print(f"✅ Planilha existente encontrada: {sheet_name}")
                return {
                    'name': sheet_name,
                    'url': sheet.url,
                    'id': sheet.id,
                    'worksheet_id': sheet.get_worksheet(0).id
                }
            except:
                print(f"⚠️ Planilha '{sheet_name}' não encontrada")

            # Se não encontrou, tentar criar uma nova usando gspread diretamente
            try:
                print(f"🔄 Tentando criar planilha usando gspread...")
                sheet = self.client.create(sheet_name)
                print(f"✅ Nova planilha criada: {sheet_name}")
                print(f"🔗 ID: {sheet.id}")

                # Compartilhar com o usuário
                try:
                    sheet.share(share_email, perm_type='user', role='writer')
                    print(f"✅ Planilha compartilhada com: {share_email}")
                except Exception as share_error:
                    print(f"⚠️ Erro ao compartilhar: {share_error}")

                # Configurar a planilha
                worksheet = sheet.get_worksheet(0)

                # Configurar cabeçalhos
                headers = [
                    "Nome do Candidato", "Email", "Telefone", "Cargo Desejado",
                    "Experiência (anos)", "Formação", "Idiomas", "Habilidades Principais",
                    "Link do Currículo", "ID do Arquivo", "Status da Análise",
                    "Pontuação Final", "Data de Inclusão", "Análise da IA"
                ]

                worksheet.update('A1:N1', [headers])

                # Formatar cabeçalhos
                try:
                    worksheet.format('A1:N1', {
                        'textFormat': {'bold': True},
                        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9},
                        'textFormat': {'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                    })
                except:
                    print("⚠️ Erro ao formatar cabeçalhos (não crítico)")

                return {
                    'name': sheet_name,
                    'url': sheet.url,
                    'id': sheet.id,
                    'worksheet_id': worksheet.id
                }

            except Exception as create_error:
                if "quota has been exceeded" in str(create_error):
                    print(
                        f"⚠️ Cota excedida. Retornando informações para criação manual")
                    return {
                        'name': sheet_name,
                        'url': f"https://docs.google.com/spreadsheets/create?title={sheet_name.replace(' ', '+')}",
                        'id': None,
                        'worksheet_id': None,
                        'error': 'quota_exceeded'
                    }
                else:
                    print(f"❌ Erro ao criar planilha: {create_error}")
                    return {
                        'name': sheet_name,
                        'url': f"https://docs.google.com/spreadsheets/create?title={sheet_name.replace(' ', '+')}",
                        'id': None,
                        'worksheet_id': None,
                        'error': 'creation_failed'
                    }

        except Exception as e:
            print(f"Erro ao criar planilha na conta do usuário: {e}")
            raise e

    def add_candidate_to_sheet(self, sheet_name: str, candidate_data: Dict[str, Any]) -> bool:
        """
        Adiciona um candidato à planilha
        """
        try:
            sheet = self.client.open(sheet_name)
            worksheet = sheet.get_worksheet(0)

            # Preparar dados do candidato
            row_data = [
                candidate_data.get('name', ''),
                candidate_data.get('email', ''),
                candidate_data.get('phone', ''),
                candidate_data.get('desired_position', ''),
                candidate_data.get('experience_years', ''),
                candidate_data.get('education', ''),
                candidate_data.get('languages', ''),
                candidate_data.get('skills', ''),
                candidate_data.get('cv_link', ''),
                candidate_data.get('file_id', ''),
                candidate_data.get('analysis_status', 'Pendente'),
                candidate_data.get('final_score', ''),
                candidate_data.get('inclusion_date', ''),
                candidate_data.get('ai_analysis', '')
            ]

            # Adicionar linha
            response = worksheet.append_row(row_data)

            # Verificar se a operação foi bem-sucedida
            if response and hasattr(response, 'get') and response.get('updates', {}).get('updatedRows', 0) > 0:
                return True
            elif response:  # Se há resposta mas não conseguimos verificar, assumir sucesso
                return True
            else:
                return False

        except Exception as e:
            print(f"Erro ao adicionar candidato à planilha: {e}")
            return False

    def update_candidate_analysis(self, sheet_name: str, candidate_name: str, analysis_data: Dict[str, Any]) -> bool:
        """
        Atualiza a análise de um candidato na planilha
        """
        try:
            sheet = self.client.open(sheet_name)
            worksheet = sheet.get_worksheet(0)

            # Encontrar a linha do candidato
            all_values = worksheet.get_all_values()
            candidate_row = None

            for i, row in enumerate(all_values):
                if row[0] == candidate_name:  # Nome do candidato na primeira coluna
                    candidate_row = i + 1  # +1 porque as linhas começam em 1
                    break

            if candidate_row:
                # Atualizar dados da análise
                updates = [
                    (f'K{candidate_row}', analysis_data.get(
                        'status', 'Analisado')),
                    (f'L{candidate_row}', analysis_data.get('score', '')),
                    (f'N{candidate_row}', analysis_data.get('ai_analysis', ''))
                ]

                for cell, value in updates:
                    worksheet.update(cell, value)

                return True
            else:
                print(f"Candidato {candidate_name} não encontrado na planilha")
                return False

        except Exception as e:
            print(f"Erro ao atualizar análise do candidato: {e}")
            return False
