# DSO-X 3000 X-Series transport bridge requirements

## Background

The DSO-X waveform path is not text-only SCPI. `:WAVeform:DATA?` returns an IEEE 488.2 definite-length **binary block** when BYTE/WORD waveform format is selected.

During 2026-08 hardware debugging, a USB-to-TCP forwarding tool was found to be converting returned waveform bytes as ASCII text. Ordinary text SCPI queries still worked, but binary waveform acquisition failed with an apparent VISA timeout inside `acquire_word_waveform()`.

The instrument and DSO-X SCPI commands were not the root cause. The forwarding layer was corrupting or delaying the binary response.

## Requirement

Any USB/GPIB/VISA-to-TCP forwarding bridge used with DSO-X waveform acquisition must operate in **binary-transparent / raw byte** mode.

It must not:

- decode returned bytes as ASCII/UTF-8 text;
- normalize line endings inside binary payloads;
- stop reading at embedded `\n` or `\r` bytes;
- append or remove bytes from the IEEE 488.2 block payload;
- convert binary samples to printable text unless the client explicitly requested ASCII waveform format.

## Diagnostic signature

A bridge configuration problem can look like this:

1. `*IDN?`, trigger queries, timebase queries and measurement queries succeed;
2. `:DIGitize` appears to run normally;
3. `:WAVeform:DATA?` / `acquire_word_waveform()` times out or returns malformed data;
4. changing trigger sweep or acquisition mode does not fix the failure.

When this pattern appears, verify the forwarding tool's raw/binary mode before changing the DSO-X driver or increasing VISA timeouts.

## Recommended waveform read path

For VISA transports, prefer a length-aware IEEE 488.2 block reader and do not wait for a text terminator after the declared binary payload. The platform `VisaTransport.query_ieee_block_bytes(..., expect_termination=False)` exists for this purpose.

## Qualification note

Text-SCPI success alone is not sufficient to qualify a transport bridge for this instrument. Hardware qualification must include at least one real BYTE/WORD waveform transfer.
