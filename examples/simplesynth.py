# ## Creating a simple synth
#
# In this example we'll create a new synth using torchsynth modules. Synth
# artchitectures can be created using a modular synthesizer paradigm by interconnecting
# individual modules that each have a unique function. We'll create a simple single
# oscillator synth with an attack-decay-sustain-release (ADSR) envelope controlling
# the amplitude in this example. More complicated architectures can be created
# using the same ideas!

# +
from typing import Optional

import torch
import IPython.display as ipd

from torchsynth.module import (
    ADSR,
    ControlRateUpsample,
    MonophonicKeyboard,
    SquareSawVCO,
    VCA,
)
from torchsynth.synth import AbstractSynth
from torchsynth.config import SynthConfig, BASE_REPRODUCIBLE_BATCH_SIZE


# -

# ### The SimpleSynth class
#
# All synths in torchsynth derive from `AbstractSynth`, which contains many helpful
# methods which include funcitonality for keeping track of children `SynthModule`s,
# creating random patches, and more. See the API documentation for `AbstractSynth` for
# more information.
#
# There are two steps involved in creating a class that derives from `Abstract Synth`:
# 1. Define the synth modules that will be used in `__init__`
# 2. Define how modules interconnect in `output`


class SimpleSynth(AbstractSynth):
    """
    A Simple Synthesizer with a SquareSaw oscillator
    and an ADSR modulating the amplitude

    Args:
        synthconfig: Synthesizer configuration that defines the
            batch_size, buffer_size, and sample_rate among other
            variables that control synthesizer functioning
    """

    def __init__(self, synthconfig: Optional[SynthConfig] = None):

        # Make sure to call __init__ in the parent AbstractSynth
        super().__init__(synthconfig=synthconfig)

        # These are all the modules that we are going to use.
        # Pass in a list of tuples with (name, SynthModule,
        # optional params dict) after we add them we will be
        # able to access them as attributes with the same name.
        self.add_synth_modules(
            [
                ("keyboard", MonophonicKeyboard),
                ("adsr", ADSR),
                ("upsample", ControlRateUpsample),
                ("vco", SquareSawVCO),
                ("vca", VCA),
            ]
        )

    def output(self) -> torch.Tensor:
        """
        This is called when we trigger the synth. We link up
        all the individual modules and pass the outputs through
        to the output of this method.
        """
        # Keyboard is parameter module, it returns parameter
        # values for the midi_f0 note value and the duration
        # that note is held for.
        midi_f0, note_on_duration = self.keyboard()

        # The amplitude envelope is generated based on note duration
        envelope = self.adsr(note_on_duration)

        # The envelope that we get from ADSR is at the control rate,
        # which is by default 100x less than the sample rate. This
        # reduced control rate is used for performance reasons.
        # We need to upsample the envelope prior to use with the VCO output.
        envelope = self.upsample(envelope)

        # Generate SquareSaw output at frequency for the midi note
        out = self.vco(midi_f0)

        # Apply the amplitude envelope to the oscillator output
        out = self.vca(out, envelope)

        return out


# That's out simple synth! Let's test it out now.
#
# If we instantiate SimpleSynth without passing in a SynthConfig object then it will
# create one with the default options. We don't need to render a full batch size for
# this example, so let's use the smallest batch size that will support reproducible
# output. All the parameters in a synth are randomly assigned values, with reprodcible
# mode on, we pass a batch_id value into our synth when calling it. The same sounds
# will always be returned for the same batch_id.

# +
# Create SynthConfig with smallest reproducible batch size.
# Reprodicible mode is on by default.
synthconfig = SynthConfig(batch_size=BASE_REPRODUCIBLE_BATCH_SIZE)
synth = SimpleSynth(synthconfig)

# If you have access to a GPU.
if torch.cuda.is_available():
    synth.to("cuda")
# -

# Now, let's make some sounds! We just call synth with a batch_id.

# +
audio = synth(0)

print(
    f"Created {audio.shape[0]} synthesizer sounds "
    f"that are each {audio.shape[1]} samples long"
)
# -

# Let's listen to some of the sounds we made

for i in range(audio.shape[0] // 4):
    ipd.display(ipd.Audio(audio[i].cpu().numpy(), rate=int(synth.sample_rate.item())))

# That's it for now -- Happy Patching!
