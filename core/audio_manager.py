"""
مدیریت صدا و موسیقی پس‌زمینه — نسخه pygame.mixer
=================================================
- کاملاً غیرقفل‌کننده — QMediaPlayer حذف شده
- موسیقی: pygame.mixer.music (یک ترک همزمان)
- SFX: pygame.mixer.Sound (چند صدای همزمان)
- فایل‌های MP3, WAV, OGG پشتیبانی می‌شوند

نسخه: 3.0.0
"""
import os

import pygame

from config import ASSETS_DIR


# ============================================================
# نگاشت صحنه → فایل صوتی
# ============================================================
SCENE_AUDIO_MAP = {
    # ویدیوی معرفی — بی‌صدا (خودش موسیقی دارد)
    "video_intro": None,

    # منو
    "menu": "menu_ambient.mp3",
    "settings": "menu_ambient.mp3",

    # مقدمه و بین‌پرده
    "demographic": "menu_ambient.mp3",
    "intro": "station_calm.mp3",
    "interlude": "station_calm.mp3",
    "night": "station_calm.mp3",

    # فازها
    "phase1": "phase_control.mp3",
    "phase2": "phase_tense.mp3",
    "phase3": "phase_control.mp3",
    "phase4": "phase_council.mp3",

    # پایان
    "council_prep": "phase_council.mp3",
    "letter_to_self": None,
    "hexaco": None,
    "results": "phase_council.mp3",
    "theater_end": "station_calm.mp3",
}


class AudioManager:
    """مدیریت صدا — Singleton با pygame.mixer"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.enabled: bool = True
        self.volume: float = 0.4

        self.current_scene: str = ""
        self.current_track: str = ""
        self._missing_tracks_logged: set = set()
        self._missing_sfx_logged: set = set()

        self._available: bool = False
        self._sfx_cache: dict = {}       # cache برای صداهای کوتاه

        self._init_mixer()

    # ================================================================
    def _init_mixer(self):
        """راه‌اندازی pygame mixer"""
        try:
            pygame.mixer.init(
                frequency=44100,
                size=-16,        # 16-bit signed
                channels=2,      # stereo
                buffer=1024,     # کمی بزرگ‌تر برای پایداری
            )
            pygame.mixer.music.set_volume(self.volume)
            self._available = True
            print("✓ AudioManager (pygame) آماده است")
        except Exception as e:
            print(f"⚠️ pygame mixer راه‌اندازی نشد: {e}")
            self._available = False

    # ================================================================
    def set_enabled(self, enabled: bool):
        """روشن/خاموش کردن صدا"""
        self.enabled = bool(enabled)
        if not self.enabled:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            print("🔇 صدا خاموش شد")
        else:
            if self.current_scene:
                self.on_scene_changed(self.current_scene)
            print("🔊 صدا روشن شد")

    # ================================================================
    def set_volume(self, volume: float):
        """تنظیم صدا"""
        self.volume = max(0.0, min(1.0, float(volume)))
        try:
            pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass

    # ================================================================
    def on_scene_changed(self, scene_name: str):
        """هنگام تغییر صحنه، موسیقی را عوض کن — بدون قفل"""
        if not self._available:
            return

        self.current_scene = scene_name

        if not self.enabled:
            return

        track_name = SCENE_AUDIO_MAP.get(scene_name)

        if track_name is None:
            self._stop_music()
            return

        # اگر همان ترک قبلی در حال پخش است، دوباره شروع نکن
        if track_name == self.current_track:
            try:
                if pygame.mixer.music.get_busy():
                    return
            except Exception:
                pass

        self._play_music(track_name)

    # ================================================================
    def _play_music(self, track_name: str):
        """پخش موسیقی — pygame این کار را سریع انجام می‌دهد"""
        path = os.path.join(ASSETS_DIR, "audio", track_name)

        if not os.path.exists(path):
            if track_name not in self._missing_tracks_logged:
                self._missing_tracks_logged.add(track_name)
                print(f"🔇 ترک '{track_name}' یافت نشد — سکوت")
            self._stop_music()
            return

        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(loops=-1)
            self.current_track = track_name
            print(f"🎵 در حال پخش: {track_name}")
        except Exception as e:
            print(f"⚠️ خطا در پخش {track_name}: {e}")

    def _stop_music(self):
        """توقف موسیقی"""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.current_track = ""

    # ================================================================
    def stop_all(self):
        """توقف کامل — هنگام بستن برنامه"""
        self._stop_music()
        self.stop_all_sfx()

    # ================================================================
    # ✅ SFX — پخش همزمان با pygame.mixer.Sound
    # ================================================================
    def play_sfx(self, sfx_name: str):
        """پخش یک افکت صوتی کوتاه"""
        if not self._available:
            return
        if not self.enabled:
            return

        sfx_map = {
            "click":      "click_button",
            "choice":     "choice_confirm",
            "toast":      "toast_appear",
            "scan":       "scan_pulse",
            "transition": "transition_whoosh",
        }
        base_name = sfx_map.get(sfx_name)
        if not base_name:
            return

        # جستجوی فایل با هر پسوند پشتیبانی‌شده
        audio_dir = os.path.join(ASSETS_DIR, "audio")
        path = None
        for ext in ("wav", "ogg", "mp3"):
            candidate = os.path.join(audio_dir, f"{base_name}.{ext}")
            if os.path.exists(candidate):
                path = candidate
                break

        if path is None:
            if base_name not in self._missing_sfx_logged:
                self._missing_sfx_logged.add(base_name)
                print(f"🔇 SFX یافت نشد: {base_name}")
            return

        try:
            # Cache کردن Sound object برای کارایی
            if path not in self._sfx_cache:
                self._sfx_cache[path] = pygame.mixer.Sound(path)

            sound = self._sfx_cache[path]
            sound.set_volume(self.volume)
            sound.play()
        except Exception as e:
            print(f"⚠️ خطا در پخش SFX {sfx_name}: {e}")

    def stop_all_sfx(self):
        """توقف همه‌ی افکت‌های کوتاه"""
        try:
            pygame.mixer.stop()
        except Exception:
            pass


# ============================================================
# نمونه‌ی سراسری
# ============================================================
_audio_manager: AudioManager | None = None


def get_audio_manager() -> AudioManager:
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager