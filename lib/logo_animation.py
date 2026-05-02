import framebuf
import time
from hardware import hw
import logo


def Logo(button):
    oled = hw.oled
    logo_fb = framebuf.FrameBuffer(
        logo.logo_data, logo.logo_width, logo.logo_height, framebuf.MONO_VLSB)

    # reveal line by line
    for row in range(logo.logo_height):
        # Draw one line from logo to OLed
        for i in range(logo.logo_width):
            # read pixel
            px = logo_fb.pixel(i, row)
            oled.pixel(i, row, px)
        # show every 2 rows
        if row % 2 == 1:
            oled.show()
            time.sleep_ms(30)

    oled.show()

    # freeze the full logo for 1 sec
    time.sleep_ms(1000)

    # blink the hold to start text
    blink = True
    last_blink = time.ticks_ms()
    btn_press = 0
    btn_held = False

    while True:
        now = time.ticks_ms()

        # Toggle blink every 500ms
        if time.ticks_diff(now, last_blink) >= 500:
            blink = not blink
            last_blink = now

            # Redraw logo
            oled.fill(0)
            oled.blit(logo_fb, 0, 0)

            # draw hold to start txt
            if blink:
                oled.text("HOLD TO START", 12, 54)

            oled.show()

        # check if button held for 500ms
        if button.value() == 0:
            if not btn_held:
                btn_held = True
                btn_press = now
            elif time.ticks_diff(now, btn_press) >= 500:
                break
        else:
            btn_held = False

    # clear the screen
    oled.fill(0)
    oled.show()
