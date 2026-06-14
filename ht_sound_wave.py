import sys
import os
import warnings
import math
import threading
import random
import numpy as np
import pygame
import soundcard as sc

# Windowsショートカット作成用のライブラリ
try:
    import win32com.client
except ImportError:
    pass

try:
    from soundcard.mediafoundation import SoundcardRuntimeWarning
    warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)
except:
    pass
warnings.filterwarnings("ignore", category=UserWarning)

# ========================================================
# 🛠️ 【管理者権限不要】初回起動時・自動ショートカット作成ロジック
# ========================================================
def create_shortcuts():
    try:
        # 自分自身の絶対パスを取得 (EXE化されても正常に動作する設定)
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
            current_dir = os.path.dirname(exe_path)
        else:
            exe_path = os.path.abspath(__file__)
            current_dir = os.path.dirname(exe_path)

        # 同じフォルダーにあるはずの icon.ico のパス
        icon_path = os.path.join(current_dir, "icon.ico")
        
        # アイコンファイルが存在しない場合はデフォルトの見た目になるため、
        # あらかじめ同じフォルダーに icon.ico を置いておくのを推奨します
        if not os.path.exists(icon_path):
            icon_path = exe_path # ない場合はEXE自身のアイコンを使用

        # 管理者権限のいらない、現在のユーザー個人のデスクトップとスタートメニュー（プログラム）のパスを取得
        desktop_dir = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        startmenu_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs')

        shortcut_targets = [
            os.path.join(desktop_dir, "HTSound wave.lnk"),
            os.path.join(startmenu_dir, "HTSound wave.lnk")
        ]

        # Windowsのシェル機能を使ってショートカットを作成
        shell = win32com.client.Dispatch("WScript.Shell")
        
        for shortcut_path in shortcut_targets:
            # すでにショートカットが存在する場合は、無駄な書き込みをパスする
            if not os.path.exists(shortcut_path):
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.TargetPath = exe_path          # 起動するEXEのパス
                shortcut.WorkingDirectory = current_dir  # 作業ディレクトリ
                shortcut.IconLocation = f"{icon_path},0" # 適用するアイコンのインデックス
                shortcut.Description = "⚡ HTSound wave Audio Engine ⚡"
                shortcut.save()
                print(f"SHORTCUT CREATED: {shortcut_path}")
    except Exception as e:
        # バックグラウンド処理のため、万が一失敗してもメインの起動を邪魔しないようにスルー
        print(f"Shortcut creation skipped: {e}")

# 起動と同時にショートカット作成を最優先で走らせる
create_shortcuts()


# ========================================================
# ⚡ メイングラフィック・オーディオエンジン (HTSound wave)
# ========================================================
pygame.init()
pygame.font.init()
info = pygame.display.Info()

WIDTH, HEIGHT = info.current_w, info.current_h
CHUNK_SIZE = 1024

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE, vsync=0)
pygame.display.set_caption("⚡ HTSound wave ⚡")
clock = pygame.time.Clock()

is_fullscreen = True

# 共有データ
shared_data = np.zeros(CHUNK_SIZE)
shared_volume = 0.0
audio_lock = threading.Lock()

# --- 【宇宙創生】3Dワープパーティクル ---
NUM_STARS = 220
stars = []
for _ in range(NUM_STARS):
    stars.append({
        "x": random.uniform(-2000, 2000),
        "y": random.uniform(-2000, 2000),
        "z": random.uniform(50, 2000),
        "color_type": random.choice([0, 1, 2])
    })

nova_radius = 0
nova_alpha = 0

# --- 音声裏部屋スレッド ---
def audio_capture_thread():
    global shared_data, shared_volume
    try:
        default_speaker = sc.default_speaker()
        loopback_mic = sc.get_microphone(id=default_speaker.id, include_loopback=True)
        with loopback_mic.recorder(samplerate=48000, blocksize=CHUNK_SIZE) as recorder:
            while True:
                try:
                    raw_data = recorder.record(numframes=CHUNK_SIZE)
                    raw_data = np.nan_to_num(raw_data, nan=0.0, posinf=0.0, neginf=0.0)
                    data = raw_data[:, 0] if raw_data.ndim > 1 else raw_data
                    
                    vol = np.sqrt(np.mean(data**2)) if len(data) > 0 else 0
                    if np.isnan(vol) or np.isinf(vol): vol = 0.0
                    
                    with audio_lock:
                        shared_data = data.copy()
                        shared_volume = vol
                except:
                    pass
    except Exception as e:
        print(f"AUDIO ERROR: {e}")

threading.Thread(target=audio_capture_thread, daemon=True).start()

angle_offset = 0
smooth_volume = 0
intro_timer = 3.0

try:
    title_font = pygame.font.SysFont("arialblack", int(HEIGHT * 0.07))
    sub_font = pygame.font.SysFont("arial", int(HEIGHT * 0.03))
except:
    title_font = pygame.font.Font(None, int(HEIGHT * 0.09))
    sub_font = pygame.font.Font(None, int(HEIGHT * 0.04))

while True:
    dt = clock.tick(0) / 1000.0  
    if dt > 0.1: dt = 0.1 
    
    actual_fps = clock.get_fps()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    WIDTH, HEIGHT = info.current_w, info.current_h
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE, vsync=0)
                else:
                    WIDTH, HEIGHT = 1280, 720
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE, vsync=0)
            elif event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
                
        elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE, vsync=0)

    with audio_lock:
        data = shared_data.copy()
        volume = shared_volume

    last_smooth = smooth_volume
    smooth_volume = smooth_volume * 0.84 + volume * 0.16

    screen.fill((2, 3, 8))
    cx, cy = WIDTH // 2, HEIGHT // 2

    if intro_timer > 0:
        intro_timer -= dt

    # スーパーノヴァ・オーラ
    if intro_timer <= 0 and smooth_volume - last_smooth > 0.06 and nova_alpha <= 0:
        nova_radius = 10
        nova_alpha = 255

    if nova_alpha > 0:
        nova_radius += int(700 * dt)
        nova_alpha -= int(400 * dt)
        if nova_alpha < 0: nova_alpha = 0
        
        if nova_radius < max(WIDTH, HEIGHT):
            ring_color = (int(nova_alpha * 0.3), int(nova_alpha * 0.5), nova_alpha)
            pygame.draw.circle(screen, ring_color, (cx, cy), nova_radius, max(1, int(5 * (nova_alpha/255))))

    # サイバーグリッド床
    grid_y = int(HEIGHT * 0.88)
    pygame.draw.line(screen, (15, 22, 45), (0, grid_y), (WIDTH, grid_y), 1)
    grid_spacing = max(40, WIDTH // 20)
    for gi in range(0, WIDTH, grid_spacing):
        target_x = cx + (gi - cx) * 1.8
        pygame.draw.line(screen, (8, 12, 32), (gi, grid_y), (int(target_x), HEIGHT), 1)

    # 3Dハイパースペース・ワープ
    if intro_timer > 0:
        warp_speed = 40 * 60.0 * dt
    else:
        warp_speed = (80 + smooth_volume * 2400) * 60.0 * dt

    for s in stars:
        prev_z = s["z"]
        s["z"] -= warp_speed
        
        if s["z"] <= 10:
            s["z"] = 2000
            s["x"] = random.uniform(-2000, 2000)
            s["y"] = random.uniform(-2000, 2000)
            prev_z = s["z"]

        focal_length = cx * 0.75
        
        sx = int(cx + (s["x"] / s["z"]) * focal_length)
        sy = int(cy + (s["y"] / s["z"]) * focal_length)
        
        psx = int(cx + (s["x"] / prev_z) * focal_length)
        psy = int(cy + (s["y"] / prev_z) * focal_length)

        if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
            distance_ratio = (2000 - s["z"]) / 2000
            size = max(1, int(1 + distance_ratio * 5))
            brightness = min(255, int(40 + distance_ratio * 215))
            
            if s["color_type"] == 0:
                color = (brightness, brightness, brightness)
            elif s["color_type"] == 1:
                color = (int(brightness * 0.6), int(brightness * 0.85), brightness)
            else:
                color = (brightness, int(brightness * 0.6), brightness)

            if intro_timer <= 0 and smooth_volume > 0.04 and (psx != sx or psy != sy):
                pygame.draw.line(screen, color, (psx, psy), (sx, sy), max(1, size // 2))
            else:
                pygame.draw.circle(screen, color, (sx, sy), size)

    # デュアルネオンウェーブ
    angle_offset += (2.5 + (smooth_volume * 5.0)) * dt
    max_allowed_amp = HEIGHT * 0.35
    
    if intro_timer > 0:
        amplitude = 25 + math.sin(angle_offset * 0.5) * 10
    else:
        amplitude = math.tanh(smooth_volume * 5.0) * max_allowed_amp
        if amplitude < 8: amplitude = 8

    main_points = []
    sub_points = []
    
    step = max(2, WIDTH // 400)
    for x in range(0, WIDTH, step):
        idx = int((x / WIDTH) * (CHUNK_SIZE - 1))
        audio_val = data[idx] if idx < len(data) else 0
        safe_audio_val = math.tanh(audio_val * 2.5) if intro_timer <= 0 else 0
        
        # メイン波
        freq_factor1 = 0.007 + (x / WIDTH) * 0.015
        y_main = (
            cy
            + math.sin(x * freq_factor1 + angle_offset) * amplitude
            + (safe_audio_val * amplitude * 0.6)
        )
        main_points.append((x, int(max(6, min(HEIGHT - 6, y_main)))))
        
        # 高音サブレーザー
        freq_factor2 = 0.02 + (x / WIDTH) * 0.03
        y_sub = (
            cy
            + math.cos(x * freq_factor2 - angle_offset * 1.2) * (amplitude * 0.38)
            + (safe_audio_val * amplitude * 0.25)
        )
        sub_points.append((x, int(max(6, min(HEIGHT - 6, y_sub)))))

    main_thickness = max(4, min(int(4 + smooth_volume * 40), 16)) if intro_timer <= 0 else 5
    sub_thickness = max(2, min(int(2 + smooth_volume * 18), 6)) if intro_timer <= 0 else 2

    if len(main_points) > 1:
        for i in range(len(main_points) - 1):
            ratio = main_points[i][0] / WIDTH
            
            r = int(255 * (1 - ratio) + 15 * ratio)
            g = int(15 * (1 - ratio) + 130 * ratio)
            b = int(70 * (1 - ratio) + 255 * ratio)
            
            try:
                pygame.draw.line(screen, (r, g, b), main_points[i], main_points[i+1], main_thickness)
                pygame.draw.line(screen, (255, 255, 255), main_points[i], main_points[i+1], max(1, main_thickness // 4))
                pygame.draw.line(screen, (10, int(190 * ratio + 40), 255), sub_points[i], sub_points[i+1], sub_thickness)
            except TypeError:
                pass

    # タイトル表示
    if intro_timer > 0:
        alpha = 255
        if intro_timer < 1.0:
            alpha = int(intro_timer * 255)

        title_text = title_font.render("⚡ HTSound wave ⚡", True, (255, 255, 255))
        shadow_text = title_font.render("⚡ HTSound wave ⚡", True, (20, 100, 255))
        sub_text = sub_font.render("SYSTEM AUDIO ENGINE ONLINE", True, (120, 140, 180))

        title_surf = pygame.Surface(title_text.get_size(), pygame.SRCALPHA)
        shadow_surf = pygame.Surface(shadow_text.get_size(), pygame.SRCALPHA)
        sub_surf = pygame.Surface(sub_text.get_size(), pygame.SRCALPHA)

        title_surf.blit(title_text, (0, 0))
        shadow_surf.blit(shadow_text, (0, 0))
        sub_surf.blit(sub_text, (0, 0))

        title_surf.set_alpha(alpha)
        shadow_surf.set_alpha(int(alpha * 0.6))
        sub_surf.set_alpha(int(alpha * 0.8))

        t_w, t_h = title_text.get_size()
        s_w, s_h = sub_text.get_size()
        
        screen.blit(shadow_surf, (cx - t_w // 2 + 4, cy - t_h // 2 - 40 + 4))
        screen.blit(title_surf, (cx - t_w // 2, cy - t_h // 2 - 40))
        screen.blit(sub_surf, (cx - s_w // 2, cy + t_h // 2 + 10))

    pygame.display.flip()
