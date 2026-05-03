import framebuf
import time
from hardware import hw
import senjougahara


def user_change_animation():
    #show Senjougahara staring for 5 sec
    oled = hw.oled
    fb = framebuf.FrameBuffer(
        senjougahara.senjougahara_data,
        senjougahara.senjougahara_width,
        senjougahara.senjougahara_height,
        framebuf.MONO_VLSB)

    oled.fill(0)
    oled.blit(fb, 0, 0)
    oled.show()

    start = time.ticks_ms()
    #staring loop
    while time.ticks_diff(time.ticks_ms(), start) < 5000:
        pass

    oled.fill(0)
    oled.show()
