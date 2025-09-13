import uuid
from streamlit_option_menu import option_menu
from analyser.database.tiny_db import AnalyserDatabase
from analyser.factories.job_factory import JobFactory
from analyser.models.job import Job
from analyser.service.llama_client import LlamaClient


DESTINATION_PATH = 'storage'
MENUS = (
    'Nova',
    'Editar',
    'Excluir'
)


class JobRoute:
    def __init__(self) -> None:
        self.llm = LlamaClient()
        self.database = AnalyserDatabase()
        self.jobs = [job.get('name') for job in self.database.jobs.all()]
        self.job = {}
        print(self.jobs)

    def render_menu(self):
        new, edition, remove = MENUS
        return option_menu(
            None,
            [new, edition, remove],
            icons=['clipboard-check', 'code-square', "clipboard2-x"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal"
        )

    def new_job_form(self, st):
        st.subheader("📋 Criar Nova Vaga")

        # Opção para criar planilha automaticamente
        create_sheet_auto = st.checkbox("Criar planilha automaticamente", value=True,
                                        help="Se marcado, uma nova planilha será criada automaticamente no Google Sheets")

        # Opção para usar planilha existente
        use_existing_sheet = st.checkbox("Usar planilha existente (se houver problemas de cota)", value=False,
                                         help="Se marcado, tentará usar uma planilha existente em vez de criar nova")

        if create_sheet_auto:
            sheet_name = st.text_input(
                'Nome da Vaga (será usado para criar a planilha)', placeholder="Ex: Desenvolvedor Python")
            if use_existing_sheet:
                st.info(
                    "ℹ️ Tentará usar planilha existente: 'Currículos - [Nome da Vaga]'")
                st.warning("⚠️ Se não encontrar, tentará criar nova")
            else:
                st.info(
                    "ℹ️ A planilha será criada automaticamente com o nome: 'Currículos - [Nome da Vaga]'")
        else:
            sheet_name = st.text_input(
                'Nome da Tabela do Google Sheets (já existente)')
            st.info("ℹ️ Use uma planilha já existente no Google Sheets")

        job_name = st.text_input('Nome da Vaga')
        main_activities = st.text_area('Atividades Principais')
        prerequisites = st.text_area('Pré Requisitos')
        differentials = st.text_area('Diferenciais')
        if st.form_submit_button('Salvar'):
            if not all([sheet_name, job_name, main_activities, prerequisites, differentials]):
                st.error(
                    'O meu querido, não tem como salvar uma vaga sem preencher os dados!')
                return

            job_dict = {
                'job_name': job_name,
                'main_activities': main_activities,
                'prerequisites': prerequisites,
                'differentials': differentials,
            }

            with st.spinner('Aguarde um momento...'):

                competence = self.llm.create_competence(job_dict)
                strategies = self.llm.create_strategies(job_dict)
                qualification = self.llm.create_qualification(job_dict)
                score_qualification = self.llm.score_competence(
                    job_dict, qualification)

                print(score_qualification)
                print(type(score_qualification))

                job_factory = JobFactory(
                    name=job_name,
                    main_activities=main_activities,
                    prerequisites=prerequisites,
                    differentials=differentials,
                    sheet_name=sheet_name,
                    competence=competence,
                    strategies=strategies,
                    qualifications=qualification,
                    score_qualification=score_qualification,
                    use_existing_sheet=use_existing_sheet,
                )
                job_factory.create()

                # Armazenar informações da planilha na sessão
                st.session_state.job_factory = job_factory
                st.session_state.show_sheet_buttons = True
                st.rerun()

        # Mostrar botões da planilha fora do formulário
        if hasattr(st.session_state, 'show_sheet_buttons') and st.session_state.show_sheet_buttons:
            job_factory = st.session_state.job_factory

            st.success('✅ Vaga criada com sucesso!')

            # Verificar se houve problema com a planilha
            if hasattr(job_factory, 'sheet_creation_error') and job_factory.sheet_creation_error:
                st.warning('⚠️ ATENÇÃO: Problema com criação da planilha!')
                st.error('💾 Cota do Google Drive excedida')
                st.info('📊 Crie manualmente a planilha no Google Sheets')
                st.info('📧 Compartilhe com: matheusbnas@gmail.com')

                # Botão para criar planilha manualmente
                if hasattr(job_factory, 'sheet_url') and job_factory.sheet_url:
                    if st.button('🔗 Criar Planilha Manualmente', type="primary"):
                        st.markdown(
                            f"[Criar Planilha]({job_factory.sheet_url})")
            else:
                st.info('📊 Planilha criada automaticamente no Google Sheets')
                st.info('📧 Compartilhada com: matheusbnas@gmail.com')

                # Botão para abrir a planilha
                if hasattr(job_factory, 'sheet_url') and job_factory.sheet_url:
                    if st.button('🔗 Abrir Planilha', type="primary"):
                        st.markdown(
                            f"[Abrir Planilha]({job_factory.sheet_url})")
                else:
                    st.info('🔗 Acesse a planilha para adicionar candidatos')

            # Botão para limpar a sessão
            if st.button('🔄 Criar Nova Vaga'):
                del st.session_state.show_sheet_buttons
                del st.session_state.job_factory
                st.rerun()

    def edition_job_form(self, st, options):
        all_sheet_names = self.database.get_all_sheet_names_in_jobs()
        print(all_sheet_names)
        job = self.database.get_job_by_name(options)
        sheet_name = st.selectbox(
            'Nome da tabela', all_sheet_names, index=all_sheet_names.index(job['sheet_name']))
        job_name = st.text_input('Nome da Vaga', value=job.get('name'))
        main_activities = st.text_area(
            'Atividades Principais', value=job.get('main_activities'))
        prerequisites = st.text_area(
            'Pré Requisitos', value=job.get('prerequisites'))
        differentials = st.text_area(
            'Diferenciais', value=job.get('differentials'))
        if st.form_submit_button('Salvar'):
            if not all([sheet_name, job_name, main_activities, prerequisites, differentials]):
                st.error(
                    'O meu querido, não tem como salvar uma vaga sem preencher os dados!')
                return

            job_schema = Job(
                id=job.get('id'),
                name=job_name,
                main_activities=main_activities,
                prerequisites=prerequisites,
                differentials=differentials,
                sheet_name=sheet_name,
                competence=job.get('competence', []),
                strategies=job.get('strategies', []),
                qualifications=job.get('qualifications', []),
                score_competence=job.get('score_competence', [])
            )

            self.database.update_job(job_schema)
            st.success('Vaga salva com sucesso')

    def remove_job_form(self, st, option):
        job_id = self.database.get_job_by_name(option).get('id')
        if st.button('Excluir') and option:
            self.database.delete_job_by_id(job_id)
            self.database.delete_all_resums_by_job_id(job_id)
            self.database.delete_all_files_by_job_id(job_id)
            self.database.delete_all_analysis_by_job_id(self.job.get('id'))
            st.success('Vaga excluida com sucesso')
