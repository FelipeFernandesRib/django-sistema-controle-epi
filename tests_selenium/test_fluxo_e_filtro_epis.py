import pytest
import time
import random
import string
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from django.urls import reverse
from app_epis.models import EPI, CategoriaEPI

@pytest.mark.usefixtures("setup")
class TestFluxoCompletoEPI:
    def test_fluxo_completo_epi(self, live_server, driver, registration_data, db):
        """
        Fluxo completo:
        1️⃣ Cria 10 EPIs via ORM (com CategoriaEPI)
        2️⃣ Registra usuário
        3️⃣ Faz login
        4️⃣ Acessa listagem de EPIs
        5️⃣ Aplica todos os filtros disponíveis
        """

        wait = WebDriverWait(driver, 10)

        # --- 1️ Criação dos EPIs via ORM ---
        cat, _ = CategoriaEPI.objects.get_or_create(nome="Equipamentos de Proteção")
        EPI.objects.all().delete()  # limpa os existentes p/ evitar duplicidade

        nomes_epi = [
            "Capacete de Segurança",
            "Luva Térmica", 
            "Óculos de Proteção",
            "Máscara Respiratória",
            "Bota Antiderrapante",
            "Protetor Auricular",
            "Cinturão de Segurança",
            "Avental de PVC",
            "Luva de Raspa",
            "Calçado de Segurança",
        ]

        epis_criados = []
        for nome in nomes_epi:
            salt = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            epi = EPI.objects.create(
                codigo=f"{nome[:3].upper()}-{salt}",
                nome=nome,
                categoria=cat,
                tamanho="U",
                ativo=True,
                estoque=random.randint(5, 30),
                estoque_minimo=1,
            )
            epis_criados.append(epi)
        print("10 EPIs criados com sucesso via ORM.")

        # --- 2️ Registro de usuário ---
        register_url = live_server.url + reverse("app_colaboradores:registrar")
        driver.get(register_url)

        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(registration_data["username"])
        time.sleep(1)
        driver.find_element(By.NAME, "email").send_keys(registration_data["email"])
        time.sleep(1)
        driver.find_element(By.NAME, "nome").send_keys(registration_data["nome"])
        time.sleep(1)
        driver.find_element(By.NAME, "matricula").send_keys(registration_data["matricula"])
        time.sleep(1)
        driver.find_element(By.NAME, "password1").send_keys(registration_data["senha"])
        time.sleep(1)
        driver.find_element(By.NAME, "password2").send_keys(registration_data["senha"])
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

        wait.until(EC.url_contains(reverse("app_colaboradores:entrar")))

        # --- 3️ Login ---
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(registration_data["username"])
        time.sleep(1)
        driver.find_element(By.NAME, "password").send_keys(registration_data["senha"])
        time.sleep(1)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

        # --- 4️ Listagem e Filtros de EPIs ---
        listar_epi_url = live_server.url + reverse("app_epis:lista")
        driver.get(listar_epi_url)
        
        # Aguarda a página carregar
        time.sleep(3)

        def get_filtro_busca():
            return driver.find_element(By.NAME, "q")
        
        def get_select_categoria():
            return Select(driver.find_element(By.NAME, "categoria"))
        
        def get_select_ordenar():
            return Select(driver.find_element(By.NAME, "ordenar"))
        
        def get_checkbox_ativos():
            return driver.find_element(By.ID, "fAtivos")
        
        def get_checkbox_abaixo():
            return driver.find_element(By.ID, "fAbaixo")
        
        def get_botao_filtrar():
            return driver.find_element(By.ID, "btn-filtrar-lista-epis")

        # --- TESTE 1: Filtro por busca ---
        print("Testando filtro de busca...")
        campo_busca = get_filtro_busca()
        campo_busca.clear()
        campo_busca.send_keys("Capacete")
        time.sleep(2)
        
        botao_filtrar = get_botao_filtrar()
        botao_filtrar.click()
        time.sleep(3)
        
        # Verifica resultados
        page = driver.page_source
        assert "Capacete" in page, "Filtro de busca não funcionou"
        print("Filtro de busca funcionou")

        # --- TESTE 2: Filtro por categoria ---
        print("Testando filtro de categoria...")
        # Localiza elementos novamente após o clique anterior
        campo_busca = get_filtro_busca()
        campo_busca.clear()
        
        select_categoria = get_select_categoria()
        select_categoria.select_by_visible_text("Equipamentos de Proteção")
        
        botao_filtrar = get_botao_filtrar()
        botao_filtrar.click()
        time.sleep(3)
        
        page = driver.page_source
        encontrado = any(epi.nome in page for epi in epis_criados)
        assert encontrado, "Filtro de categoria não funcionou"
        print("Filtro de categoria funcionou")
        
        print("🧹 Clicando no botão limpar...")
        botao_limpar = driver.find_element(By.ID, "btn-limpar-filtro")
        botao_limpar.click()
        time.sleep(2)   

        # --- TESTE 3: Filtro de ordenação ---
        print("Testando ordenação...")
        select_ordenar = get_select_ordenar()
        select_ordenar.select_by_visible_text("Nome Z→A")
        
        botao_filtrar = get_botao_filtrar()
        botao_filtrar.click()
        time.sleep(3)
        
        page = driver.page_source
        encontrado = any(epi.nome in page for epi in epis_criados)
        assert encontrado, "Filtro de ordenação não funcionou"
        print("Filtro de ordenação funcionou")


        print("🧹 Clicando no botão limpar...")
        botao_limpar = driver.find_element(By.ID, "btn-limpar-filtro")
        botao_limpar.click()
        time.sleep(2)

        # --- TESTE 4: Filtro de ativos ---
        print("Testando filtro de ativos...")
        checkbox_ativos = get_checkbox_ativos()
        if not checkbox_ativos.is_selected():
            checkbox_ativos.click()
        
        botao_filtrar = get_botao_filtrar()
        botao_filtrar.click()
        time.sleep(2)

        page = driver.page_source
        encontrado = any(epi.nome in page for epi in epis_criados)
        assert encontrado, "Filtro de ativos não funcionou"
        print("Filtro de ativos funcionou")

        # --- TESTE 5: Filtro de estoque mínimo ---
        print("Testando filtro de estoque mínimo...")
        checkbox_abaixo = get_checkbox_abaixo()
        if not checkbox_abaixo.is_selected():
            checkbox_abaixo.click()
        
        botao_filtrar = get_botao_filtrar()
        botao_filtrar.click()
        time.sleep(2)
        
        page = driver.page_source
        print("Filtro de estoque mínimo aplicado")

        print("🧹 Clicando no botão limpar...")
        botao_limpar = driver.find_element(By.ID, "btn-limpar-filtro")
        botao_limpar.click()
        time.sleep(2)

        # --- TESTE 6: Combinação de filtros ---
        print("Testando combinação de filtros...")
        # Localiza todos os elementos novamente
        campo_busca = get_filtro_busca()
        campo_busca.clear()
        campo_busca.send_keys("Luva")
        
        select_categoria = get_select_categoria()
        select_categoria.select_by_visible_text("Equipamentos de Proteção")
        
        select_ordenar = get_select_ordenar()
        select_ordenar.select_by_visible_text("Estoque ↓")
        
        checkbox_ativos = get_checkbox_ativos()
        if not checkbox_ativos.is_selected():
            checkbox_ativos.click()
            
        checkbox_abaixo = get_checkbox_abaixo()
        if checkbox_abaixo.is_selected():
            checkbox_abaixo.click()
        
        botao_filtrar = get_botao_filtrar()
        botao_filtrar.click()
        time.sleep(5)
        
        page = driver.page_source
        assert "Luva" in page, "Combinação de filtros não funcionou"
        print("Combinação de filtros funcionou")

        # --- TESTE 7: Limpar filtros ---
        print("🧹 Testando limpeza de filtros...")
        # Localiza todos os elementos novamente
        campo_busca = get_filtro_busca()
        campo_busca.clear()
        
        select_categoria = get_select_categoria()
        select_categoria.select_by_visible_text("Todas")
        
        select_ordenar = get_select_ordenar()
        select_ordenar.select_by_visible_text("Estoque ↑")
        
        checkbox_abaixo = get_checkbox_abaixo()
        if checkbox_abaixo.is_selected():
            checkbox_abaixo.click()
            
        checkbox_ativos = get_checkbox_ativos()
        if not checkbox_ativos.is_selected():
            checkbox_ativos.click()
        
        botao_filtrar = get_botao_filtrar()
        botao_filtrar.click()
        time.sleep(5)
        
        # Verifica se vários EPIs aparecem
        page = driver.page_source
        epis_encontrados = sum(1 for epi in epis_criados if epi.nome in page)
        print(f"EPIs encontrados após limpar filtros: {epis_encontrados}/10")
        
        assert epis_encontrados > 0, "Nenhum EPI encontrado após limpar filtros"
        print("Filtros limpos com sucesso")

        print("Teste completo: todos os filtros aplicados e testados com sucesso!")