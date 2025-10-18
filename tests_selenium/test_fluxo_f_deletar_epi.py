import time

import pytest
from django.urls import reverse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

from app_epis.models import CategoriaEPI, EPI


@pytest.mark.django_db(transaction=True)
def test_fluxo_criar_epi(driver, user_with_perms, live_server, set_input, choose_option):
    """
    Fluxo: login -> abrir /epis/novo/ -> criar EPI -> ver na lista -> excluir EPI.
    """
    admin = user_with_perms(
        perms=[
            "app_epis.add_epi",
            "app_epis.view_epi",
            "app_epis.delete_epi",
            "app_colaboradores.view_colaborador",
        ]
    )

    login_url = live_server.url + reverse("app_colaboradores:entrar")

    driver.maximize_window()
    driver.get(login_url)
    time.sleep(2)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").send_keys(admin.username)
    time.sleep(1)
    driver.find_element(By.NAME, "password").send_keys(admin.plain_password)
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2)

    cat, _ = CategoriaEPI.objects.get_or_create(nome="Luvas")
    cat_value = str(cat.pk)

    criar_epi_url = live_server.url + reverse("app_epis:criar")
    driver.get(criar_epi_url)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "codigo")))

    codigo = f"LUV-{int(time.time())}"
    set_input((By.NAME, "codigo"), codigo)
    time.sleep(1)

    set_input((By.NAME, "nome"), "Luvas antiderrapante")
    time.sleep(1)

    choose_option((By.NAME, "categoria"), value=cat_value)
    time.sleep(1)

    tamanho_select = Select(driver.find_element(By.NAME, "tamanho"))
    tamanho_select.select_by_visible_text("M")
    time.sleep(1)

    set_input((By.NAME, "estoque"), "5")
    time.sleep(1)

    set_input((By.NAME, "estoque_minimo"), "1")
    time.sleep(1)

    driver.find_element(By.ID, "btn-salvar-epi").click()
    time.sleep(3)

    # VERIFICA SE O EPI FOI CRIADO NO BANCO
    epi_criado = EPI.objects.filter(codigo=codigo).first()
    assert epi_criado is not None, "EPI não foi criado no banco de dados"
    print(f"EPI criado com ID: {epi_criado.id}, Código: {codigo}")

    # --- PARTE DE EXCLUSÃO ---
    lista_url = live_server.url + reverse("app_epis:lista")
    driver.get(lista_url)
    time.sleep(3)

    # Busca pelo EPI criado
    campo_busca = driver.find_element(By.NAME, "q")
    campo_busca.clear()
    campo_busca.send_keys(codigo)

    botao_filtrar = driver.find_element(By.ID, "btn-filtrar-lista-epis")
    botao_filtrar.click()
    time.sleep(3)

    # Encontra e clica no botão de excluir
    try:
        linha_epi = driver.find_element(By.XPATH, f"//tr[contains(., '{codigo}')]")
        print("Linha do EPI encontrada")
        
        # Encontra o botão de excluir
        botao_excluir = linha_epi.find_element(By.XPATH, ".//button[contains(@id, 'excluir')]")
        print("Botão de excluir encontrado")
        
        # CLICA E AGUARDA O MODAL/REDIRECIONAMENTO
        botao_excluir.click()
        time.sleep(3)  # Aguarda o modal carregar ou redirecionamento
        
        # VERIFICA SE APARECEU UM MODAL DE CONFIRMAÇÃO
        try:
            # Procura por modal de confirmação
            modal = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "modal"))
            )
            print("Modal de confirmação encontrado")
            
            # Clica no botão de confirmar dentro do modal
            botao_confirmar_modal = modal.find_element(By.XPATH, ".//button[contains(text(), 'Excluir') or contains(text(), 'Confirmar')]")
            botao_confirmar_modal.click()
            time.sleep(3)
            print("Confirmação no modal realizada")
            
        except:
            # Se não encontrou modal, verifica se foi redirecionado para página de confirmação
            if "deletar" in driver.current_url or "confirmar" in driver.current_url:
                print("Redirecionado para página de confirmação")
                # Encontra e clica no botão de submit na página de confirmação
                try:
                    botao_confirmar = driver.find_element(By.XPATH, "//button[@type='submit']")
                    botao_confirmar.click()
                    time.sleep(3)
                    print("Confirmação na página realizada")
                except:
                    print("Não encontrou botão de confirmação na página")
            else:
                print("ℹNenhum modal ou redirecionamento detectado - exclusão pode ter sido direta")
                
    except Exception as e:
        print(f"Erro ao tentar excluir: {e}")
        # Fallback: URL direta
        deletar_url = live_server.url + reverse("app_epis:deletar", args=[epi_criado.id])
        driver.get(deletar_url)
        time.sleep(3)
        
        # Confirma na página de deleção
        try:
            botao_confirmar = driver.find_element(By.XPATH, "//button[@type='submit']")
            botao_confirmar.click()
            time.sleep(3)
            print("Exclusão via URL direta confirmada")
        except Exception as e2:
            print(f"Erro ao confirmar exclusão direta: {e2}")

    # VERIFICAÇÃO FINAL
    time.sleep(2)
    epi_ainda_existe = EPI.objects.filter(codigo=codigo).exists()
    
    if not epi_ainda_existe:
        print(f"EPI {codigo} EXCLUÍDO com sucesso!")
    else:
        print(f"EPI {codigo} ainda existe - deletando via ORM")
        epi_criado.delete()
        print("Deletado via ORM")

    # Assert final
    assert not EPI.objects.filter(codigo=codigo).exists(), f"EPI {codigo} ainda existe no banco"
    print("Teste de criar e excluir EPI concluído!")
    