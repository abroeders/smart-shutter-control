# Calibration

## Why

Most shutter modules only know the travel time between the ends. At "50 %" they have run half that time,
but the shutter is then **lower** than half way, for three reasons:

1. **The roller grows.** Each turn winds more slat length as the roll gets thicker, so the shutter moves
   slowly at first and faster later.
2. **Slat gaps.** From closed, the first part of the travel only pulls the slats apart (light through the
   gaps) before the bottom bar lifts from the sill.
3. **Direction.** If the motor is slower going up than going down, the same module position is a different
   height in each direction.

After calibration the integration's cover and card show the **real** position (the height of the opening
below the bottom bar, as a share of the window), and a target of 50 % ends half way, from either direction.
Fully open and fully closed always use the module's own ends (its limit switches).

## The assistant

*Reconfigure → Calibrate* on the shutter. Have a tape measure ready. Automatic control of that shutter pauses
while the assistant runs. It does not run during a storm.

1. **Window height** in cm (or leave it empty and give openings in % of the window).
2. The shutter **closes**.
3. **Lift point:** the shutter moves up in steps of 2 % and asks *Has the bottom bar left the sill?* until you
   say yes. The step before is the **slit**: all gaps open, bar still on the sill.
4. **Four points going up**, spread over the travel above the lift point. At each point: measure the opening
   below the bottom bar.
5. The shutter **opens fully**, then the same points **going down**.
6. **Result:** the module position for 50 % in each direction, and how well the model fits. A difference of
   more than about 5 % between the directions means the motor is faster one way.

With a **motor power sensor** the assistant sees when the motor stops; without one it first measures the
**travel time** (open fully, then close fully) and waits the expected time for each move.

**Add a calibration point** moves the shutter from closed (↑) or from open (↓) to a module position you
choose, and asks for the opening. Use it to improve a curve without measuring everything again.

## The model

Per direction the real opening `o` follows from the module position `m` as a clipped quadratic,
`o = a·m + b·m² − c`, fitted to your points (the roller grows linearly with each turn; `c` is the gap zone).
When that does not fit within 3 % of the window, a smooth monotone curve through the points is used instead.
The sensor *Calibration* shows the model and the fit per direction.

To send a real position the integration inverts the curve of the direction the shutter will move in, and
picks the nearest whole module position.
