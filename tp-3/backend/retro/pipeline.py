"""
The pipeline: builds the list of steps from the options and runs them. Given.

    photo → SquareCrop → Shrink → [GradientMap] → PaletteMap | FloydSteinberg → [Frame] → Enlarge

It also helps while the steps are being written:
  - a step that raises StepNotImplemented is skipped ("pending");
  - if an essential step (Shrink) is pending, or a step fails, the following
    ones are not run ("blocked");
  - every result is checked (array, uint8, 3 channels, expected size), so a
    wrong step is reported by its name instead of breaking a later one.
"""

import logging
from dataclasses import dataclass
from typing import Literal

import numpy as np

from retro.exceptions import PhotoTooSmall, StepFailed, StepNotImplemented
from retro.palettes import DEFAULT_PALETTE, PALETTES
from retro.steps import Enlarge, FloydSteinberg, Frame, GradientMap, PaletteMap, Shrink, SquareCrop, Step

log = logging.getLogger("retro")

OUTPUT_SIZE = 512                 # side of the avatar, in screen pixels
PIXEL_SIZES = (16, 32, 64, 128)   # side of the avatar, in "big" pixels (all divide OUTPUT_SIZE)
MAX_FRAME = 4                     # thickest frame, in big pixels

Status = Literal["done", "pending", "blocked", "failed"]


@dataclass(frozen=True)
class AvatarOptions:
    pixels: int = 32                 # one of PIXEL_SIZES
    palette: str = DEFAULT_PALETTE   # a key of PALETTES
    dithering: bool = False          # FloydSteinberg instead of PaletteMap
    frame: int = 0                   # thickness of the frame (0 = no frame)


@dataclass(frozen=True)
class StepResult:
    step: Step
    status: Status
    image: np.ndarray | None = None  # what the step returned (only when "done")
    message: str = ""                # why it is pending, blocked or failed


@dataclass(frozen=True)
class Trace:
    """What happened in each step of a run."""

    photo: np.ndarray
    results: list[StepResult]

    @property
    def image(self) -> np.ndarray:
        """The last image produced: the avatar, if every step is done."""
        done = [r.image for r in self.results if r.status == "done"]
        return done[-1] if done else self.photo

    @property
    def complete(self) -> bool:
        return all(r.status == "done" for r in self.results)

    @property
    def failure(self) -> StepResult | None:
        return next((r for r in self.results if r.status == "failed"), None)


def describe(step: Step) -> str:
    name = type(step).__name__
    return f"el paso {step.number} ({name})" if step.number else name


class AvatarMaker:
    def __init__(self, output_size: int = OUTPUT_SIZE) -> None:
        self.output_size = output_size

    def steps(self, options: AvatarOptions) -> list[Step]:
        """The steps for these options, in the order they are applied."""
        palette = PALETTES[options.palette]
        steps: list[Step] = [SquareCrop(), Shrink(options.pixels)]
        if palette.monochrome:
            steps.append(GradientMap(palette))
        steps.append(FloydSteinberg(palette) if options.dithering else PaletteMap(palette))
        if options.frame > 0:
            steps.append(Frame(palette.darkest, options.frame))
        steps.append(Enlarge(self.output_size // options.pixels))
        return steps

    def run(self, photo: np.ndarray, options: AvatarOptions) -> Trace:
        """Applies every step to the photo and records what happened in each one."""
        height, width = photo.shape[:2]
        if min(height, width) < options.pixels:
            raise PhotoTooSmall(
                f"La foto mide {width}×{height}: para un avatar de {options.pixels}×{options.pixels} "
                f"tiene que tener al menos {options.pixels} píxeles de lado.")

        image, results, waiting = photo, [], None
        for step in self.steps(options):
            if waiting is not None:
                message = f"Se saltea hasta que funcione {describe(waiting)}."
                results.append(StepResult(step, "blocked", message=message))
                continue
            try:
                output = step.apply(image)
            except StepNotImplemented as exc:
                results.append(StepResult(step, "pending", message=str(exc)))
                if step.essential:
                    waiting = step
                continue
            except Exception as exc:  # a bug in a step: say which one
                log.exception("%s failed", describe(step))
                message = f"Falló {describe(step)}: {type(exc).__name__}: {exc}"
                results.append(StepResult(step, "failed", message=message))
                waiting = step
                continue

            problem = check_output(step, image, output)
            if problem:
                results.append(StepResult(step, "failed", message=problem))
                waiting = step
                continue
            image = output
            results.append(StepResult(step, "done", image))
        return Trace(photo, results)

    def make(self, photo: np.ndarray, options: AvatarOptions) -> np.ndarray:
        """The avatar (or as far as the implemented steps get). Raises StepFailed if a step fails."""
        trace = self.run(photo, options)
        if trace.failure:
            raise StepFailed(trace.failure.message)
        return trace.image


def check_output(step: Step, image: np.ndarray, output: object) -> str | None:
    """Why `output` is not a valid result of `step`, or None if it is."""
    who = describe(step)
    who = who[0].upper() + who[1:]
    if not isinstance(output, np.ndarray):
        return f"{who} devolvió {type(output).__name__}: tiene que devolver un array de numpy."
    if output.ndim != 3 or output.shape[2] != 3:
        return f"{who} devolvió un array de forma {output.shape}: tiene que ser (alto, ancho, 3)."
    if output.dtype != np.uint8:
        return f"{who} devolvió dtype {output.dtype}: tiene que ser uint8 (np.clip y .astype(np.uint8))."
    expected = step.output_shape(*image.shape[:2])
    if output.shape[:2] != expected:
        got = f"{output.shape[1]}×{output.shape[0]}"
        return f"{who} devolvió una imagen de {got}: se esperaba {expected[1]}×{expected[0]}."
    return None
