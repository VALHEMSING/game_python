"""
Módulo encargado de la síntesis, carga y reproducción de audio y música.
Utiliza NumPy para la generación procedural de ondas y Pygame para la reproducción.
"""
from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import Iterable

import numpy as np
import pygame

from mi_doom.config import (
    MUSIC_DIR,
    MUSIC_VOLUME,
    SAMPLE_RATE,
    SFX_VOLUME,
    SOUNDS_DIR,
)

SOUND_NAMES = (
    "pistol",
    "shotgun",
    "machinegun",
    "impact",
    "damage",
    "death",
    "pickup",
    "door",
    "key",
    "menu",
    "switch",
    "exit",
)

MUSIC_THEME_NAME = "theme"


class AudioManager:
    """
    Gestiona la reproducción de efectos de sonido (SFX) y música de fondo.
    Se encarga de cargar los archivos generados y controlar los volúmenes.
    """

    def __init__(self) -> None:
        """Inicializa el gestor de audio, generando los assets si es necesario."""
        self.enabled = pygame.mixer.get_init() is not None
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.current_music: str | None = None

        self.sfx_volume = SFX_VOLUME
        self.music_volume = MUSIC_VOLUME

        if not self.enabled:
            return

        try:
            generate_all_audio(force=False)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        self._load_sounds()

    def _load_sounds(self) -> None:
        """Carga los efectos de sonido desde el disco en memoria."""
        for name in SOUND_NAMES:
            path = SOUNDS_DIR / f"{name}.wav"

            if not path.exists():
                continue

            try:
                sound = pygame.mixer.Sound(str(path))
                sound.set_volume(self.sfx_volume)
                self.sounds[name] = sound
            except Exception:  # pylint: disable=broad-exception-caught
                continue

    def play_sfx(self, name: str) -> None:
        """Reproduce un efecto de sonido específico por su nombre."""
        if not self.enabled:
            return

        sound = self.sounds.get(name)
        if sound is None:
            return

        sound.set_volume(self.sfx_volume)
        sound.play()

    def play_music(self, name: str = MUSIC_THEME_NAME) -> None:
        """Reproduce una pista de música en bucle."""
        if not self.enabled:
            return

        path = MUSIC_DIR / f"{name}.wav"

        if not path.exists():
            return

        if self.current_music == name:
            return

        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
            self.current_music = name
        except Exception:  # pylint: disable=broad-exception-caught
            self.current_music = None

    def stop_music(self) -> None:
        """Detiene la reproducción de la música de fondo."""
        if not self.enabled:
            return

        try:
            pygame.mixer.music.stop()
            self.current_music = None
        except Exception:  # pylint: disable=broad-exception-caught
            self.current_music = None

    def set_sfx_volume(self, volume: float) -> None:
        """Ajusta el volumen global de los efectos de sonido."""
        self.sfx_volume = max(0.0, min(1.0, volume))

        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)

    def set_music_volume(self, volume: float) -> None:
        """Ajusta el volumen global de la música de fondo."""
        self.music_volume = max(0.0, min(1.0, volume))

        if self.enabled:
            try:
                pygame.mixer.music.set_volume(self.music_volume)
            except Exception:  # pylint: disable=broad-exception-caught
                pass


def generate_all_audio(force: bool = False) -> None:
    """Genera y guarda en disco todos los archivos WAV de SFX y música."""
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    for name in SOUND_NAMES:
        path = SOUNDS_DIR / f"{name}.wav"

        if path.exists() and not force:
            continue

        samples = generate_sound(name)
        _write_wav(path, samples)

    music_path = MUSIC_DIR / f"{MUSIC_THEME_NAME}.wav"

    if not music_path.exists() or force:
        samples = _make_theme()
        _write_wav(music_path, samples)


def generate_sound(name: str) -> np.ndarray:
    """Genera el array de muestras NumPy para un sonido específico."""
    if name == "pistol":
        return _make_pistol()
    if name == "shotgun":
        return _make_shotgun()
    if name == "machinegun":
        return _make_machinegun()
    if name == "impact":
        return _make_impact()
    if name == "damage":
        return _make_damage()
    if name == "death":
        return _make_death()
    if name == "pickup":
        return _make_pickup()
    if name == "door":
        return _make_door()
    if name == "key":
        return _make_key()
    if name == "menu":
        return _make_menu()
    if name == "switch":
        return _make_switch()
    if name == "exit":
        return _make_exit()

    return _make_menu()


def _seconds_to_samples(duration: float) -> int:
    """Convierte una duración en segundos a un número entero de muestras."""
    return max(1, int(duration * SAMPLE_RATE))


def _decay_envelope(duration: float, decay: float) -> np.ndarray:
    """Genera una envolvente de decaimiento exponencial."""
    count = _seconds_to_samples(duration)
    t = np.linspace(0.0, duration, count, endpoint=False)
    return np.exp(-t * decay).astype(np.float32)


def _tone(
    frequency: float,
    duration: float,
    volume: float = 1.0,
    waveform: str = "sine",
) -> np.ndarray:
    """Genera un tono puro con la forma de onda especificada."""
    count = _seconds_to_samples(duration)
    t = np.linspace(0.0, duration, count, endpoint=False)
    phase = 2.0 * math.pi * frequency * t

    if waveform == "square":
        samples = np.sign(np.sin(phase))
    elif waveform == "saw":
        samples = 2.0 * (t * frequency - np.floor(0.5 + t * frequency))
    else:
        samples = np.sin(phase)

    return (samples * volume).astype(np.float32)


def _sweep(
    start_frequency: float,
    end_frequency: float,
    duration: float,
    volume: float = 1.0,
    waveform: str = "sine",
) -> np.ndarray:
    """Genera un barrido de frecuencia (chirp) entre dos valores."""
    count = _seconds_to_samples(duration)
    frequencies = np.linspace(start_frequency, end_frequency, count, dtype=np.float32)
    phase = 2.0 * math.pi * np.cumsum(frequencies) / SAMPLE_RATE

    if waveform == "square":
        samples = np.sign(np.sin(phase))
    elif waveform == "saw":
        normalized = phase / (2.0 * math.pi)
        samples = 2.0 * (normalized - np.floor(0.5 + normalized))
    else:
        samples = np.sin(phase)

    return (samples * volume).astype(np.float32)


def _noise(duration: float, volume: float = 1.0, seed: int = 0) -> np.ndarray:
    """Genera ruido blanco pseudoaleatorio."""
    count = _seconds_to_samples(duration)
    rng = np.random.default_rng(seed)
    samples = rng.uniform(-1.0, 1.0, count).astype(np.float32)
    return samples * volume


def _sequence(
    notes: Iterable[tuple[float, float]],
    waveform: str = "sine",
    volume: float = 0.5,
    gap: float = 0.0,
) -> np.ndarray:
    """Genera una secuencia de notas musicales consecutivas."""
    total_duration = sum(duration for _, duration in notes)
    total_duration += gap * max(0, len(tuple(notes)) - 1)

    result = np.zeros(_seconds_to_samples(total_duration), dtype=np.float32)
    offset = 0
    gap_samples = _seconds_to_samples(gap)

    for frequency, duration in notes:
        count = _seconds_to_samples(duration)

        if frequency > 0.0:
            tone = _tone(frequency, duration, volume, waveform)
            envelope = _decay_envelope(duration, 7.0)
            end = min(offset + count, len(result))
            result[offset:end] += tone[: end - offset] * envelope[: end - offset]

        offset += count + gap_samples

    return result


def _make_pistol() -> np.ndarray:
    """Sintetiza el sonido de disparo de la pistola."""
    duration = 0.14
    sweep = _sweep(720.0, 160.0, duration, 0.70, "square")
    noise = _noise(duration, 0.25, seed=11)
    envelope = _decay_envelope(duration, 22.0)
    return (sweep + noise) * envelope


def _make_shotgun() -> np.ndarray:
    """Sintetiza el sonido de disparo de la escopeta."""
    duration = 0.32
    noise = _noise(duration, 0.80, seed=22)
    low = _sweep(95.0, 55.0, duration, 0.30, "square")
    envelope = _decay_envelope(duration, 7.0)
    return (noise + low) * envelope


def _make_machinegun() -> np.ndarray:
    """Sintetiza el sonido de disparo de la ametralladora."""
    duration = 0.08
    sweep = _sweep(520.0, 180.0, duration, 0.65, "square")
    noise = _noise(duration, 0.22, seed=33)
    envelope = _decay_envelope(duration, 28.0)
    return (sweep + noise) * envelope


def _make_impact() -> np.ndarray:
    """Sintetiza el sonido de impacto de bala."""
    duration = 0.10
    noise = _noise(duration, 0.50, seed=44)
    tone = _tone(260.0, duration, 0.25, "sine")
    envelope = _decay_envelope(duration, 20.0)
    return (noise + tone) * envelope


def _make_damage() -> np.ndarray:
    """Sintetiza el sonido de daño recibido por el jugador."""
    duration = 0.28
    sweep = _sweep(220.0, 65.0, duration, 0.70, "square")
    envelope = _decay_envelope(duration, 8.0)
    return sweep * envelope


def _make_death() -> np.ndarray:
    """Sintetiza el sonido de muerte del jugador o enemigo."""
    duration = 0.60
    sweep = _sweep(200.0, 35.0, duration, 0.75, "saw")
    envelope = _decay_envelope(duration, 4.0)
    return sweep * envelope


def _make_pickup() -> np.ndarray:
    """Sintetiza el sonido de recogida de objeto."""
    return _sequence(
        [
            (660.0, 0.06),
            (880.0, 0.08),
        ],
        waveform="sine",
        volume=0.50,
    )


def _make_door() -> np.ndarray:
    """Sintetiza el sonido de apertura de puerta."""
    duration = 0.45
    noise = _noise(duration, 0.16, seed=55)
    sweep = _sweep(140.0, 70.0, duration, 0.45, "square")
    envelope = _decay_envelope(duration, 5.0)
    return (noise + sweep) * envelope


def _make_key() -> np.ndarray:
    """Sintetiza el sonido de recogida de llave."""
    return _sequence(
        [
            (880.0, 0.05),
            (1174.66, 0.05),
            (1567.98, 0.07),
        ],
        waveform="sine",
        volume=0.45,
    )


def _make_menu() -> np.ndarray:
    """Sintetiza el sonido de navegación de menú."""
    return _tone(520.0, 0.06, 0.40, "sine") * _decay_envelope(0.06, 12.0)


def _make_switch() -> np.ndarray:
    """Sintetiza el sonido de activación de interruptor."""
    click = _tone(1100.0, 0.05, 0.50, "square")
    noise = _noise(0.05, 0.12, seed=66)
    envelope = _decay_envelope(0.05, 25.0)
    return (click + noise) * envelope


def _make_exit() -> np.ndarray:
    """Sintetiza el sonido de salida de nivel."""
    return _sequence(
        [
            (523.25, 0.07),
            (659.25, 0.07),
            (783.99, 0.07),
            (1046.50, 0.10),
        ],
        waveform="sine",
        volume=0.50,
    )


def _make_theme() -> np.ndarray:
    """Sintetiza la música de fondo principal del juego."""
    step_duration = 0.16
    steps = 32
    total_duration = step_duration * steps
    buffer = np.zeros(_seconds_to_samples(total_duration), dtype=np.float32)

    bass_pattern = [
        110.00,
        110.00,
        130.81,
        146.83,
    ] * 8

    lead_pattern = [
        0.0,
        0.0,
        220.00,
        0.0,
        261.63,
        0.0,
        196.00,
        0.0,
        0.0,
        0.0,
        329.63,
        0.0,
        293.66,
        0.0,
        220.00,
        0.0,
    ] * 2

    for index in range(steps):
        start_time = index * step_duration

        bass_frequency = bass_pattern[index]
        _add_note(
            buffer,
            start_time,
            bass_frequency,
            0.14,
            "square",
            0.28,
        )

        lead_frequency = lead_pattern[index]
        if lead_frequency > 0.0:
            _add_note(
                buffer,
                start_time,
                lead_frequency,
                0.12,
                "square",
                0.16,
            )

    return _fade_edges(buffer, 0.03)


def _add_note(
    buffer: np.ndarray,
    start_time: float,
    frequency: float,
    duration: float,
    waveform: str,
    volume: float,
) -> None:
    """Añade una nota sintetizada a un buffer de audio existente."""
    if frequency <= 0.0:
        return

    start = int(start_time * SAMPLE_RATE)
    tone = _tone(frequency, duration, volume, waveform)
    envelope = _decay_envelope(duration, 8.0)
    tone *= envelope

    end = min(start + len(tone), len(buffer))
    sample_count = end - start

    if sample_count <= 0:
        return

    buffer[start:end] += tone[:sample_count]


def _fade_edges(samples: np.ndarray, fade_duration: float) -> np.ndarray:
    """Aplica un fade-in y fade-out suave a los extremos de la muestra."""
    fade_samples = _seconds_to_samples(fade_duration)
    fade_in = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
    fade_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)

    samples[:fade_samples] *= fade_in
    samples[-fade_samples:] *= fade_out

    return samples


def _write_wav(path: Path, samples: np.ndarray) -> None:
    """Escribe un array de muestras NumPy en un archivo WAV en disco."""
    samples = np.asarray(samples, dtype=np.float32)

    if samples.size == 0:
        samples = np.zeros(SAMPLE_RATE // 10, dtype=np.float32)

    peak = float(np.max(np.abs(samples)))
    if peak > 0.0:
        samples = samples / peak * 0.80

    int16_samples = (samples * 32767.0).astype("<i2")

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)  # pylint: disable=no-member
        wav_file.setsampwidth(2)  # pylint: disable=no-member
        wav_file.setframerate(SAMPLE_RATE)  # pylint: disable=no-member
        wav_file.writeframes(int16_samples.tobytes())  # pylint: disable=no-member
