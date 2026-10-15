import pygame
import numpy as np


class NokiaSoundManager:
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate
        self.eat_sound = None
        self.game_over_sound = None
        self.click_sound = None
        self.startup_sound = None
        self.enabled = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)
            self.sample_rate = pygame.mixer.get_init()[0]
            self.enabled = True
        except Exception:
            self.enabled = False

        if self.enabled:
            self.eat_sound = self._generate_munch_sound()
            self.game_over_sound = self._generate_game_over_tone()
            self.click_sound = self._generate_beep(frequency=660, duration=0.04)
            self.startup_sound = self._generate_note_sequence(
                [659, 784, 659, 988, 1318],
                duration_per_note=0.1,
                volume=7000,
                gap=0.025,
            )

    def _generate_beep(self, frequency, duration):
        """Generates a classic 8-bit square wave tone in 2D stereo array format."""
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)

        wave = np.sign(np.sin(2 * np.pi * frequency * t))
        audio = (wave * 12000).astype(np.int16)
        stereo_audio = np.column_stack((audio, audio))
        return pygame.sndarray.make_sound(stereo_audio)

    def _generate_game_over_tone(self):
        """Generates a 3-note descending 8-bit game over sequence in stereo format."""
        notes = [440, 330, 220]
        duration_per_note = 0.12
        return self._generate_note_sequence(notes, duration_per_note=duration_per_note, volume=12000)

    def _generate_munch_sound(self):
        """Creates one loud, crisp bite with a short low crunchy thump."""
        rng = np.random.default_rng(7)
        duration = 0.22
        count = int(self.sample_rate * duration)
        t = np.arange(count, dtype=np.float32) / self.sample_rate
        noise = rng.normal(0, 1, count)
        crisp_crunch = noise - np.concatenate(([0.0], noise[:-1])) * 0.94
        soft_crunch = np.convolve(noise, np.ones(7) / 7, mode="same")
        envelope = np.exp(-t * 17) * np.minimum(t / 0.001, 1.0)
        jaw_thump = np.sin(2 * np.pi * (115 - 55 * t / duration) * t)
        audio = (0.74 * crisp_crunch + 0.16 * soft_crunch + 0.10 * jaw_thump)
        audio *= envelope
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio *= 26000 / peak
        mono_audio = audio.astype(np.int16)
        stereo_audio = np.column_stack((mono_audio, mono_audio))
        return pygame.sndarray.make_sound(stereo_audio)

    def _generate_note_sequence(
        self, notes, duration_per_note=0.08, volume=12000, gap=0.0
    ):
        full_audio = []
        for freq in notes:
            n_samples = int(self.sample_rate * duration_per_note)
            t = np.linspace(0, duration_per_note, n_samples, False)
            wave = np.sign(np.sin(2 * np.pi * freq * t))
            fade_samples = max(1, int(self.sample_rate * 0.008))
            envelope = np.ones(n_samples)
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
            full_audio.append((wave * envelope * volume).astype(np.int16))
            if gap:
                full_audio.append(
                    np.zeros((int(self.sample_rate * gap),), dtype=np.int16)
                )

        combined_audio = np.concatenate(full_audio)
        stereo_audio = np.column_stack((combined_audio, combined_audio))
        return pygame.sndarray.make_sound(stereo_audio)

    def play_eat(self):
        if self.eat_sound is not None:
            self.eat_sound.play()

    def play_game_over(self):
        if self.game_over_sound is not None:
            self.game_over_sound.play()

    def play_click(self):
        if self.click_sound is not None:
            self.click_sound.play()

    def play_startup(self):
        if self.startup_sound is not None:
            self.startup_sound.play()

        