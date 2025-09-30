import re
import os
from playwright.sync_api import sync_playwright, expect

def run_verification(playwright):
    # Asumimos que la agenda está en una URL predecible del panel de WP
    # y que el usuario ya está logueado (esto es una limitación del entorno de prueba)
    # Si no hay un servidor corriendo, usamos una ruta de archivo local como fallback.
    base_url = 'http://localhost:8888' # URL típica de un entorno de desarrollo local de WP
    agenda_page_url = f'{base_url}/wp-admin/admin.php?page=veterinalia-appointment-schedule'

    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # Intentamos navegar a la página de la agenda con un timeout corto
        page.goto(agenda_page_url, timeout=5000, wait_until='networkidle')
        print(f"Navegación exitosa a {agenda_page_url}")

    except Exception as e:
        print(f"No se pudo navegar al servidor local. Error: {e}")
        print("Intentando cargar el archivo de plantilla local como fallback...")
        # Construir la ruta absoluta al archivo para que sea una URL válida
        file_path = os.path.abspath('templates/modules/agenda-module.php')
        file_url = f'file://{file_path}'
        print(f"Cargando URL de archivo local: {file_url}")
        page.goto(file_url)
        page.wait_for_timeout(1000) # Esperar a que el DOM inicial se cargue

    # 1. Hacer clic en la primera tarjeta de cita que encontremos
    print("Buscando una tarjeta de cita...")
    first_appointment_card = page.locator('.appointment-card-vision').first
    expect(first_appointment_card).to_be_visible(timeout=10000)
    print("Cita encontrada. Haciendo clic...")
    first_appointment_card.click()

    # 2. Verificar que el modal de detalles de la cita aparece
    print("Verificando que el modal de detalles de la cita está visible...")
    appointment_modal = page.locator('#appointment-modal')
    expect(appointment_modal).to_be_visible()
    expect(page.get_by_role("heading", name=re.compile("Detalles de la Cita|Consulta de seguimiento", re.IGNORECASE))).to_be_visible()

    # 3. Hacer clic en el botón "Completar y Registrar"
    print("Haciendo clic en 'Completar y Registrar'...")
    complete_button = page.get_by_role("button", name="Completar y Registrar")
    expect(complete_button).to_be_enabled()
    complete_button.click()

    # 4. Verificar la transición al formulario de la bitácora
    print("Verificando la transición al formulario de la bitácora...")
    # El título del modal debe cambiar
    expect(page.get_by_role("heading", name="Registrar en Bitácora")).to_be_visible(timeout=10000)

    # El formulario debe aparecer
    logbook_form = page.locator('#logbook-form-dynamic')
    expect(logbook_form).to_be_visible()

    # Deben aparecer los nuevos botones
    expect(page.get_by_role("button", name="Guardar Bitácora")).to_be_visible()
    expect(page.get_by_role("button", name="Omitir")).to_be_visible()
    print("Transición verificada correctamente.")

    # 5. Tomar la captura de pantalla final
    screenshot_path = 'jules-scratch/verification/modal_transition_verified.png'
    page.screenshot(path=screenshot_path)
    print(f"Captura de pantalla guardada en: {screenshot_path}")

    # Cerrar todo
    context.close()
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_verification(playwright)