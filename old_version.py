import pyautogui
import pygetwindow
import keyboard
import time
import random
import sys

# --- CONFIGURACIÓN PRINCIPAL ---
WINDOW_TITLE = "Xbox"
TARGET_WIDTH = 1280
TARGET_HEIGHT = 720
STOP_KEY = "f10"
running = True

# --- Lógica para detener el bot ---
def stop_script():
    global running
    print("Tecla de detención presionada. Saliendo...")
    running = False

keyboard.add_hotkey(STOP_KEY, stop_script)

# --- Funciones de Utilidad ---

def get_game_window():
    """Encuentra y devuelve el objeto de la ventana del juego."""
    try:
        window = pygetwindow.getWindowsWithTitle(WINDOW_TITLE)[0]
        return window
    except IndexError:
        return None

def is_window_active(window):
    """Verifica si la ventana del juego está activa."""
    if not window:
        return False
    return window.isActive

def resize_window_if_needed(window):
    """Redimensiona la ventana si no tiene el tamaño objetivo."""
    if window.width != TARGET_WIDTH or window.height != TARGET_HEIGHT:
        print(f"Redimensionando ventana a {TARGET_WIDTH}x{TARGET_HEIGHT}...")
        window.resizeTo(TARGET_WIDTH, TARGET_HEIGHT)
        time.sleep(1) # Dar tiempo a que la ventana se ajuste

def check_pixel_color(x, y, expected_rgb, tolerance=15):
    """
    Verifica si el color de un píxel en la pantalla coincide con un color esperado.
    Las coordenadas son relativas a la pantalla.
    """
    try:
        pixel_rgb = pyautogui.pixel(x, y)
        return (abs(pixel_rgb[0] - expected_rgb[0]) <= tolerance and
                abs(pixel_rgb[1] - expected_rgb[1]) <= tolerance and
                abs(pixel_rgb[2] - expected_rgb[2]) <= tolerance)
    except Exception as e:
        # Esto puede pasar si las coordenadas están fuera de la pantalla
        return False

def click_in_range(x1, y1, x2, y2, win_pos):
    """Hace clic en una posición aleatoria dentro de un rectángulo."""
    rand_x = random.randint(x1, x2) + win_pos[0]
    rand_y = random.randint(y1, y2) + win_pos[1]
    pyautogui.click(rand_x, rand_y)
    time.sleep(0.5)

# --- Funciones de Detección de Estado (AQUÍ DEBES ACTUALIZAR LAS COORDENADAS) ---

def is_main_menu(win_pos):
    # TODO: ¡NECESITAS ACTUALIZAR ESTAS COORDENADAS Y COLORES!
    p1 = check_pixel_color(win_pos[0] + 1247, win_pos[1] + 620, (255, 199, 22))
    p2 = check_pixel_color(win_pos[0] + 1275, win_pos[1] + 680, (255, 186, 16))
    return p1 or p2

def is_game_lost(win_pos):
    # TODO: ¡NECESITAS ACTUALIZAR ESTAS COORDENADAS Y COLORES!
    p1 = check_pixel_color(win_pos[0] + 152, win_pos[1] + 646, (247, 81, 63))
    p2 = check_pixel_color(win_pos[0] + 23, win_pos[1] + 646, (244, 76, 57))
    return p1 or p2

def is_get_reward(win_pos):
    # TODO: ¡NECESITAS ACTUALIZAR ESTAS COORDENADAS Y COLORES!
    p1 = check_pixel_color(win_pos[0] + 1027, win_pos[1] + 638, (77, 214, 27))
    p2 = check_pixel_color(win_pos[0] + 1190, win_pos[1] + 670, (72, 207, 26))
    return p1 or p2

def is_game_running(win_pos):
    # TODO: ¡NECESITAS ACTUALIZAR ESTAS COORDENADAS Y COLORES!
    p1 = check_pixel_color(win_pos[0] + 637, win_pos[1] + 297, (255, 255, 255))
    p2 = check_pixel_color(win_pos[0] + 641, win_pos[1] + 297, (255, 255, 255))
    return p1 and p2

def is_game_results(win_pos):
    # TODO: ¡NECESITAS ACTUALIZAR ESTAS COORDENADAS Y COLORES!
    p1 = check_pixel_color(win_pos[0] + 451, win_pos[1] + 74, (83, 30, 166))
    p2 = check_pixel_color(win_pos[0] + 825, win_pos[1] + 73, (73, 25, 147))
    return p1 and p2

# --- Funciones de Acción ---

def click_play_game(win_pos):
    print("Haciendo clic en 'Jugar'...")
    # TODO: ¡NECESITAS ACTUALIZAR ESTAS COORDENADAS!
    click_in_range(1027, 620, 1227, 687, win_pos)

def click_get_reward(win_pos):
    print("Reclamando recompensa...")
    # TODO: ¡NECESITAS ACTUALIZAR ESTAS COORDENADAS!
    click_in_range(1027, 638, 1190, 670, win_pos)

def leave_game():
    print("Saliendo de la partida perdida...")
    pyautogui.press('esc')
    time.sleep(1)

def simulate_gameplay():
    """Simula movimientos aleatorios para permanecer AFK."""
    print("Simulando jugabilidad...")
    pyautogui.keyDown('w') # Empezar a correr
    time.sleep(random.uniform(1.0, 2.5))

    action = random.choice(['left', 'right', 'jump', 'run'])
    if action == 'left':
        pyautogui.keyDown('a')
        time.sleep(random.uniform(0.5, 1.5))
        pyautogui.keyUp('a')
    elif action == 'right':
        pyautogui.keyDown('d')
        time.sleep(random.uniform(0.5, 1.5))
        pyautogui.keyUp('d')
    elif action == 'jump':
        pyautogui.press('space')
    
    # Dejar de correr
    pyautogui.keyUp('w')
    time.sleep(random.uniform(0.1, 0.5))

# --- Bucle Principal del Bot ---

def main():
    print("Iniciando bot de Stumble Guys para la app Xbox...")
    print(f"Presiona '{STOP_KEY}' para detener.")

    game_window = get_game_window()
    if not game_window:
        print(f"Error: No se encontró la ventana con el título '{WINDOW_TITLE}'.")
        sys.exit()
        
    print("Ventana encontrada. Trayendo al frente...")
    game_window.activate()
    time.sleep(1)
    resize_window_if_needed(game_window)

    while running:
        if not is_window_active(game_window):
            print("Ventana del juego no está activa, esperando...")
            time.sleep(3)
            continue
        
        # Obtenemos la posición de la ventana en cada iteración por si se mueve
        win_pos = (game_window.left, game_window.top)

        # La lógica es un gran if/elif/else para priorizar acciones
        if is_game_lost(win_pos):
            leave_game()
        elif is_get_reward(win_pos):
            click_get_reward(win_pos)
        elif is_game_running(win_pos):
            simulate_gameplay()
        elif is_game_results(win_pos):
            print("Esperando en la pantalla de resultados...")
            time.sleep(3) # Solo esperar
        elif is_main_menu(win_pos):
            print("En el menú principal, iniciando nueva partida.")
            click_play_game(win_pos)
            time.sleep(5) # Esperar a que empiece la búsqueda
        else:
            print("Estado no reconocido, esperando...")
            # Aquí podrías agregar más detecciones (anuncios, subidas de nivel, etc.)
        
        time.sleep(1.5) # Pausa entre cada ciclo de detección

if __name__ == "__main__":
    main()