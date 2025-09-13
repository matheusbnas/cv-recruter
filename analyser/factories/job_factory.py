import uuid
from analyser.models.job import Job
from analyser.database.tiny_db import AnalyserDatabase
from analyser.service.sheet_creator import SheetCreator

DATABASE = AnalyserDatabase()


class JobFactory:
    def __init__(self,
                 name: str,
                 main_activities: str,
                 prerequisites: str,
                 differentials: str,
                 sheet_name: str,
                 competence: list,
                 strategies: list,
                 qualifications: list,
                 score_qualification: list,
                 use_existing_sheet: bool = False,
                 ):
        self._validate_fields(name, main_activities,
                              prerequisites, differentials, sheet_name)

        self.name = name
        self.main_activities = main_activities
        self.prerequisites = prerequisites
        self.differentials = differentials
        self.sheet_name = sheet_name
        self.competence = competence
        self.strategies = strategies
        self.qualifications = qualifications
        self.score_qualification = score_qualification
        self.sheet_creation_error = False
        self.use_existing_sheet = use_existing_sheet

    def _validate_fields(self, *fields):
        for field in fields:
            if not field.strip():
                raise ValueError("Fields cannot be empty strings.")

    def create(self) -> Job:
        # Criar planilha automaticamente se não existir
        sheet_creator = SheetCreator()
        self.sheet_url = None  # Armazenar URL da planilha

        try:
            sheet_info = sheet_creator.create_job_sheet(
                self.name, use_existing=self.use_existing_sheet)
            # Usar o nome da planilha criada
            actual_sheet_name = sheet_info['name']
            print(f"Planilha criada automaticamente: {actual_sheet_name}")

            # Armazenar URL da planilha se disponível
            if 'url' in sheet_info and sheet_info['url']:
                self.sheet_url = sheet_info['url']
                print(f"🔗 URL da planilha: {self.sheet_url}")

            # Verificar se houve erro de cota excedida
            if 'error' in sheet_info and sheet_info['error'] == 'quota_exceeded':
                print(f"⚠️ ATENÇÃO: Cota do Google Drive excedida!")
                print(f"📊 Crie manualmente a planilha: {actual_sheet_name}")
                print(f"🔗 Link para criar: {sheet_info['url']}")
                print(f"📧 Compartilhe com: matheusbnas@gmail.com")
                # Marcar que houve erro para a interface
                self.sheet_creation_error = True
                # Armazenar URL para criação manual
                self.sheet_url = sheet_info['url']

        except Exception as e:
            print(f"Erro ao criar planilha: {e}")
            # Usar o nome fornecido pelo usuário como fallback
            actual_sheet_name = self.sheet_name

        job = Job(
            id=str(uuid.uuid4()),
            name=self.name,
            main_activities=self.main_activities,
            prerequisites=self.prerequisites,
            differentials=self.differentials,
            sheet_name=actual_sheet_name,
            competence=self.competence,
            strategies=self.strategies,
            qualifications=self.qualifications,
            score_competence=self.score_qualification,
        )
        DATABASE.jobs.insert(job.model_dump())
        return job
