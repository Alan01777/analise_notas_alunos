import pandas as pd
import re
import streamlit as st
import altair as alt
import io

st.set_page_config(layout='wide')
# ----------------------------------------------------------------------
# GABARITO OFICIAL
correct_answers = {
    'Q1': 'D', 'Q2': 'B', 'Q3': 'A', 'Q4': 'C', 'Q5': 'C',
    'Q6': 'A', 'Q7': 'B', 'Q8': 'B', 'Q9': 'A', 'Q10': 'C'
}

# Mapeamento de Questão para Descritor
question_descriptor_map = {
    'Q1': 'D1', 'Q2': 'D1', 'Q3': 'D3', 'Q4': 'D3', 'Q5': 'D4',
    'Q6': 'D4', 'Q7': 'D6', 'Q8': 'D6', 'Q9': 'D14', 'Q10': 'D14'
}

# Descrições dos Descritores (Exemplo - você pode expandir ou ajustar conforme necessário)
descriptor_descriptions = {
    'D1': 'Identificar a localização/movimentação de objeto, em mapas, croquis e outras representações gráficas.',
    'D3': 'Identificar propriedades comuns e diferenças entre figuras bidimensionais e tridimensionais, relacionando-as com suas planificações.',
    'D4': 'Reconhecer e utilizar características do sistema de numeração decimal, como agrupamentos e valor posicional.',
    'D6': 'Associar operações de adição, subtração, multiplicação, divisão e potenciação a problemas.',
    'D14': 'Identificar a localização de números naturais na reta numérica.'
}

# ----------------------------------------------------------------------

# Contagem de questões por descritor para calcular percentagens
descriptor_question_counts = {}
for q, d in question_descriptor_map.items():
    descriptor_question_counts[d] = descriptor_question_counts.get(d, 0) + 1

st.title('Análise de Desempenho por Descritor')
st.markdown(
    """
    Esta ferramenta analisa o desempenho dos alunos por **descritor**, consolidando os dados
    de **múltiplas planilhas** dentro de um arquivo Excel (cada planilha representando uma escola/turma).
    Identifique pontos fortes e fracos para direcionar suas ações pedagógicas.
    """
)

# Use st.file_uploader to allow users to upload Excel file
uploaded_file = st.file_uploader(
    "Faça upload do seu arquivo Excel (.xlsx) com múltiplas planilhas:",
    type=["xlsx", "xls"]
)

# Estrutura para armazenar dados detalhados por planilha e descritor
all_performance_data = []
all_sheets = {}

if uploaded_file:
    st.sidebar.title("Configurações")
    
    try:
        # Read all sheets from the Excel file
        all_sheets = pd.read_excel(uploaded_file, sheet_name=None)
        
        st.success(f"Arquivo Excel carregado com sucesso! Encontradas {len(all_sheets)} planilhas.")
        
        # Display sheet names
        st.write("**Planilhas encontradas:**")
        # Ensure sheet names don't cause horizontal overflow in this display
        sheet_names_display = ", ".join([f"**{name}**" for name in list(all_sheets.keys())])
        st.markdown(f"<div style='word-wrap: break-word;'>{sheet_names_display}</div>", unsafe_allow_html=True)

        # Process each sheet
        for sheet_name, df in all_sheets.items():
            # Using a placeholder for long sheet names for internal processing if needed
            # Excel sheet names have a limit of 31 chars, so usually they won't be excessively long.
            # However, for display in charts, we'll manage potential overflow.
            
            num_students = len(df)
            if num_students == 0:
                st.warning(f"A planilha '{sheet_name}' não contém dados de alunos. Pulando análise.")
                continue
            
            sheet_correct_per_descriptor = {d: 0 for d in set(question_descriptor_map.values())}
            
            for col in df.columns:
                # Look for columns that match the question pattern (Q1, Q2, etc.)
                # Handle both 'Q1' and 'Q1 (D1)' formats
                match = re.match(r'^Q\d+', str(col))
                if match:
                    question_number = match.group(0)  # Extract 'Q1', 'Q2', etc.
                    descriptor = question_descriptor_map.get(question_number)

                    if descriptor and question_number in correct_answers:
                        correct_answer = correct_answers[question_number]
                        # Count correct answers for this question
                        if col in df.columns:
                            # Handle potential NaN values and ensure string comparison
                            correct_count = df[col].fillna('').astype(str).str.upper().eq(correct_answer.upper()).sum()
                            sheet_correct_per_descriptor[descriptor] += correct_count
                        else:
                            st.warning(f"Coluna '{col}' esperada para {question_number} não encontrada em '{sheet_name}'.")
            
            # Add performance data for the current sheet
            for descriptor, correct_sum in sheet_correct_per_descriptor.items():
                total_possible_correct = num_students * descriptor_question_counts[descriptor]
                percentage = (correct_sum / total_possible_correct * 100) if total_possible_correct > 0 else 0
                
                all_performance_data.append({
                    'Planilha/Escola': sheet_name,
                    'Descritor': descriptor,
                    'Acertos': correct_sum,
                    'Total Possível': total_possible_correct,
                    'Percentual de Acertos': percentage,
                    'Número de Alunos': num_students
                })

    except Exception as e:
        st.error(f"Erro ao processar o arquivo Excel: {e}")
        st.error("Certifique-se de que o arquivo é um Excel válido (.xlsx ou .xls) e que a estrutura das planilhas está correta.")
        st.stop()
    
    # Check if any data was processed
    if not all_performance_data:
        st.warning("Nenhum dado válido processado do arquivo Excel. Verifique o formato das suas planilhas.")
        st.stop()

    # Convert the list of dictionaries into a pandas DataFrame
    df_all_performance = pd.DataFrame(all_performance_data)

    # Allow selection if multiple sheets are processed
    if len(all_sheets) > 1:
        selected_sheet = st.sidebar.selectbox(
            "Selecione a Planilha/Escola para Detalhes:",
            ["Geral (Todas as Escolas)"] + list(all_sheets.keys())
        )
    else:
        selected_sheet = list(all_sheets.keys())[0] if all_sheets else "Geral (Todas as Escolas)"
        st.sidebar.write(f"Planilha única carregada: **{selected_sheet}**")

    # ---
    st.markdown("---")
    st.header('Análise de Desempenho Global')

    st.markdown(
        """
        Nesta seção, você visualiza o desempenho consolidado de **todas as escolas/turmas**
        em relação a cada descritor. Isso oferece uma visão geral dos pontos fortes e
        das áreas que precisam de mais atenção no currículo ou metodologia de ensino.
        """
    )
    # Calculate overall correct answers and percentages for each descriptor (general)
    overall_descriptor_performance = df_all_performance.groupby('Descritor').agg(
        Total_Acertos=('Acertos', 'sum'),
        Total_Possivel=('Total Possível', 'sum')
    ).reset_index()
    overall_descriptor_performance['Percentual de Acertos'] = (
        overall_descriptor_performance['Total_Acertos'] / overall_descriptor_performance['Total_Possivel'] * 100
    )

    st.subheader('Acertos e Percentuais por Descritor (Geral)')
    st.dataframe(overall_descriptor_performance.sort_values(by='Descritor').round(2))

    st.markdown(
        """
        ### Gráfico: Percentual de Acertos por Descritor (Todas as Escolas)
        Este gráfico de barras mostra o **percentual médio de acertos** para cada descritor,
        considerando todas as escolas juntas.
        * **Como funciona:** Para cada descritor, somamos o total de acertos de todas as questões
            relacionadas a ele, em todas as escolas. Em seguida, dividimos pelo total possível de
            acertos (número de alunos * número de questões do descritor) e multiplicamos por 100.
        * **Como interpretar:** Barras mais altas indicam descritores onde os alunos, em geral,
            tiveram um bom desempenho. Barras mais baixas podem sinalizar descritores que
            necessitam de reforço pedagógico. Passe o mouse sobre as barras para ver detalhes.
        """
    )
    # Bar Chart: Percentage of Correct Answers by Descriptor (Overall)
    chart_overall_percentage = (
        alt.Chart(overall_descriptor_performance)
        .mark_bar()
        .encode(
            x=alt.X('Descritor', sort=None, title='Descritor', axis=alt.Axis(labelLimit=120, labelAngle=45)),  # Limit label to 120 pixels
            y=alt.Y('Percentual de Acertos', title='Percentual de Acertos (%)'),
            tooltip=[
                'Descritor', 
                alt.Tooltip('Percentual de Acertos', format='.2f', title='Percentual de Acertos (%)'),
                alt.Tooltip('Total_Acertos', title='Acertos Totais'),
                alt.Tooltip('Total_Possivel', title='Total Possível')
            ],
            color=alt.Color('Descritor', legend=None)
        )
        .properties(title='Percentual de Acertos por Descritor (Todas as Escolas)')
        .interactive()
    )
    st.altair_chart(chart_overall_percentage, use_container_width=True)

    # ---
    st.markdown("---")
    st.header('Análise Detalhada por Planilha/Escola')

    if selected_sheet == "Geral (Todas as Escolas)":
        st.markdown(
            """
            Nesta seção, você pode comparar o desempenho geral de cada escola
            ou detalhar o desempenho por descritor entre elas.
            """
        )
        # Bar Chart: Overall Percentage of Correct Answers per School
        st.subheader('Percentual Geral de Acertos por Escola')
        overall_school_performance = df_all_performance.groupby('Planilha/Escola').agg(
            Total_Acertos_Geral=('Acertos', 'sum'),
            Total_Possivel_Geral=('Total Possível', 'sum')
        ).reset_index()
        overall_school_performance['Percentual Geral de Acertos'] = (
            overall_school_performance['Total_Acertos_Geral'] / overall_school_performance['Total_Possivel_Geral'] * 100
        )

        st.markdown(
            """
            ### Gráfico: Percentual Geral de Acertos por Escola
            Este gráfico apresenta o **desempenho geral de cada escola/turma**,
            independentemente do descritor.
            * **Como funciona:** Para cada escola, somamos o total de acertos de
                todas as questões e dividimos pelo total possível de acertos de todas
                as questões, multiplicando por 100.
            * **Como interpretar:** Permite identificar rapidamente quais escolas
                estão com desempenho acima ou abaixo da média geral.
            """
        )

        # Data table for school performance
        st.dataframe(overall_school_performance.round(2))

        chart_overall_school = (
            alt.Chart(overall_school_performance)
            .mark_bar()
            .encode(
                x=alt.X('Planilha/Escola', sort=None, title='Planilha/Escola', axis=alt.Axis(labelLimit=120, labelAngle=45)), # Limit label to 120 pixels
                y=alt.Y('Percentual Geral de Acertos', title='Percentual Geral de Acertos (%)'),
                tooltip=[
                    'Planilha/Escola',
                    alt.Tooltip('Percentual Geral de Acertos', format='.2f', title='Percentual Geral de Acertos (%)'),
                    alt.Tooltip('Total_Acertos_Geral', title='Acertos Totais'),
                    alt.Tooltip('Total_Possivel_Geral', title='Total Possível')
                ],
                color=alt.Color('Planilha/Escola', legend=None)
            )
            .properties(title='Percentual Geral de Acertos por Escola')
            .interactive()
        )
        st.altair_chart(chart_overall_school, use_container_width=True)

        st.subheader('Comparação Detalhada por Descritor entre Escolas')
        st.markdown(
            """
            ### Tabela e Mapa de Calor: Comparação Detalhada por Descritor entre Escolas
            Esta tabela e o mapa de calor subsequente mostram o **percentual de acertos de cada escola
            para cada descritor individualmente**.
            * **Como funciona:** Os dados são organizados de forma que cada linha representa um descritor
                e cada coluna, uma escola, exibindo o percentual de acertos.
            * **Como interpretar:** Permite uma análise granular, identificando quais descritores
                são desafios específicos para determinadas escolas e quais são pontos fortes.
                O mapa de calor visualiza essa comparação, onde cores mais escuras (ou mais quentes,
                dependendo da escala de cor) indicam maiores percentuais de acertos.
            """
        )
        
        # Create a pivot table for better visualization
        comparison_pivot = df_all_performance.pivot_table(
            index='Descritor', 
            columns='Planilha/Escola', 
            values='Percentual de Acertos', 
            fill_value=0
        ).round(2)
        
        st.dataframe(comparison_pivot)
        
        # Heatmap-style chart for comparison
        df_melted = df_all_performance[['Planilha/Escola', 'Descritor', 'Percentual de Acertos']].copy()
        
        chart_heatmap = (
            alt.Chart(df_melted)
            .mark_rect()
            .encode(
                x=alt.X('Planilha/Escola:O', title='Escola', axis=alt.Axis(labelLimit=120, labelAngle=45)), # Limit label to 120 pixels
                y=alt.Y('Descritor:O', title='Descritor'),
                color=alt.Color('Percentual de Acertos:Q', 
                              scale=alt.Scale(scheme='viridis'), 
                              title='% Acertos'),
                tooltip=[
                    'Planilha/Escola', 
                    'Descritor',
                    alt.Tooltip('Percentual de Acertos', format='.2f', title='% Acertos')
                ]
            )
            .properties(
                title='Mapa de Calor: Percentual de Acertos por Descritor e Escola',
                width=600,
                height=450
            )
            .interactive()
        )
        st.altair_chart(chart_heatmap, use_container_width=True)
    
    else:
        # Show details for the selected sheet
        st.subheader(f'Desempenho Detalhado para: {selected_sheet}')
        st.markdown(
            f"""
            Esta seção exibe o desempenho específico da escola **{selected_sheet}**
            em cada descritor.
            """
        )
        df_selected_sheet = df_all_performance[df_all_performance['Planilha/Escola'] == selected_sheet].copy()
        
        st.dataframe(df_selected_sheet[['Descritor', 'Acertos', 'Total Possível', 'Percentual de Acertos']].round(2))

        st.markdown(
            """
            ### Gráfico: Percentual de Acertos por Descritor (Escola Selecionada)
            Este gráfico de barras detalha o **percentual de acertos para cada descritor**
            especificamente na escola selecionada.
            * **Como funciona:** Para cada descritor, calculamos o total de acertos
                dos alunos da escola selecionada e dividimos pelo total possível de acertos
                para aquele descritor na mesma escola.
            * **Como interpretar:** Ajuda a identificar os pontos fortes e fracos
                da escola em cada habilidade avaliada pelos descritores, permitindo
                intervenções pedagógicas mais direcionadas.
            """
        )

        chart_selected_sheet = (
            alt.Chart(df_selected_sheet)
            .mark_bar()
            .encode(
                x=alt.X('Descritor', sort=None, title='Descritor', axis=alt.Axis(labelLimit=120, labelAngle=45)),  # Limit label to 120 pixels
                y=alt.Y('Percentual de Acertos', title='Percentual de Acertos (%)'),
                tooltip=[
                    'Planilha/Escola', 
                    'Descritor',
                    alt.Tooltip('Percentual de Acertos', format='.2f', title='Percentual de Acertos (%)'),
                    alt.Tooltip('Acertos', title='Acertos'),
                    alt.Tooltip('Total Possível', title='Total Possível')
                ],
                color=alt.Color('Descritor', legend=None)
            )
            .properties(title=f'Percentual de Acertos por Descritor ({selected_sheet})')
            .interactive()
        )
        st.altair_chart(chart_selected_sheet, use_container_width=True)


        # Show individual student data for the selected sheet
        if st.checkbox(f"Mostrar dados individuais dos alunos - {selected_sheet}"):
            st.subheader(f'Dados Individuais dos Alunos - {selected_sheet}')
            selected_df = all_sheets[selected_sheet]
            st.dataframe(selected_df)

    st.markdown(
        """
        ---
        **Instruções de Uso:**
        1.  Prepare um arquivo Excel (.xlsx) com uma planilha para cada escola/turma.
        2.  Cada planilha deve ter colunas para as questões (Q1, Q2, Q3, etc.).
        3.  As respostas dos alunos devem estar nas colunas correspondentes.
        4.  O sistema calculará automaticamente os percentuais de acerto por descritor.
        
        **Lembrete**: Os cálculos são baseados no gabarito oficial que você forneceu.
        """
    )
else:
    st.info("Por favor, faça upload do arquivo Excel (.xlsx) para iniciar a análise.")
    st.markdown(
        """
        ### Como preparar seu arquivo Excel:
        
        1.  **Estrutura do arquivo**: Crie um arquivo Excel com múltiplas planilhas.
        2.  **Nome das planilhas**: Cada planilha deve ter o nome da escola/turma.
            * **Dica:** Nomes de planilhas no Excel são limitados a 31 caracteres. Para melhor visualização,
                mantenha-os concisos.
        3.  **Colunas**: Use as colunas Q1, Q2, Q3, ..., Q10 para as respostas.
        4.  **Dados**: Cada linha representa um aluno com suas respostas.
        
        **Exemplo de estrutura:**
        ```
        Planilha 1: "Alfredo Santos"
        ALUNO          | Q1 | Q2 | Q3 | ... | Q10
        João Silva     | A  | B  | C  | ... | D
        Maria Santos   | D  | B  | A  | ... | C
        
        Planilha 2: "José Bonifácio"
        ALUNO          | Q1 | Q2 | Q3 | ... | Q10
        Pedro Costa    | D  | A  | A  | ... | C
        Ana Lima       | D  | B  | B  | ... | D
        ```
        """
    )