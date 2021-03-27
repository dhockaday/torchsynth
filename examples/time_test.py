# +
import torch
import torch.tensor as T

from torchsynth.globals import SynthGlobals
from torchsynth.synth import Voice
# -

if torch.cuda.is_available():
    device = 'cuda'
else:
    device = 'cpu'

synthglobals64 = SynthGlobals(
    batch_size=T(64), sample_rate=T(44100), buffer_size=T(4 * 44100)
)
voice = Voice(synthglobals=synthglobals64).to(device)

with torch.no_grad():
    # %timeit voice()
