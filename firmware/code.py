# SPDX-FileCopyrightText: 2022 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
import analogio
import asyncio
import board
import digitalio
import keypad
import pwmio
import time

import hsl_rgb

# デモ中と動作中を表すクラス
class Mode:
    def __init__(self) -> None:
        self.demo = True

# modeスイッチの状態を読み取る
async def monitor_mode_pin(mode):
    with keypad.Keys((board.D9,), value_when_pressed=False, pull=True) as keys:
        while True:
            event = keys.events.get()
            if event and event.released:
                    mode.demo = not mode.demo

            await asyncio.sleep(0)

# LEDを制御する
# CircuitPythonではポーリングしかできない
async def control_led(mode):
    led_r = pwmio.PWMOut(board.D6, frequency=5000, duty_cycle=0)
    led_g = pwmio.PWMOut(board.D5, frequency=5000, duty_cycle=0)
    led_b = pwmio.PWMOut(board.D4, frequency=5000, duty_cycle=0)

    slider_r = analogio.AnalogIn(board.A3)
    slider_g = analogio.AnalogIn(board.A2)
    slider_b = analogio.AnalogIn(board.A1)

    def ad_to_pwm(ad_value):
        # ボリューム最小で500程度、最大で65300ほどなのでスケールを変換する
        slider_min = 500
        slider_max = 65300
        
        pwm = round((ad_value - slider_min) / (slider_max - slider_min) * 65536)
        if pwm < 0:
            pwm = 0
        elif pwm > 65535:
            pwm = 65535

        return(pwm)

    def ad_to_pwm_log(ad_value):
        # 指数関数的にPWM値に変換する
        slider_min = 500
        slider_max = 65300
        slider_delta = slider_max - slider_min

        if ad_value > slider_max:
            ad_value = slider_max
        elif ad_value < slider_min:
            ad_value = slider_min

        x = ad_value - slider_min

        pwm = int(65535 / 80 * (pow(9, 2*x/slider_delta) - 1))

        return pwm

    h = 0.0
    s = 100
    l = 50

    while True:
        if mode.demo:
            (r, g, b) = hsl_rgb.hsl_to_rgb(h, s, l)
            led_r.duty_cycle = min(int(r * 65535 / 255), 65535)
            led_g.duty_cycle = min(int(g * 65535 / 255), 65535)
            led_b.duty_cycle = min(int(b * 65535 / 255), 65535)

            h = h + 2
            if h >= 360:
                h = h - 360
        else:
            # led_r.duty_cycle = ad_to_pwm(slider_r.value)
            # led_g.duty_cycle = ad_to_pwm(slider_g.value)
            # led_b.duty_cycle = ad_to_pwm(slider_b.value)
            led_r.duty_cycle = ad_to_pwm_log(slider_r.value)
            led_g.duty_cycle = ad_to_pwm_log(slider_g.value)
            led_b.duty_cycle = ad_to_pwm_log(slider_b.value)
        
        await asyncio.sleep(0.02)

# バッテリーをモニターし、残量に応じてPower LEDを制御する
# 状態が頻繁に変わるのを防ぐため、電圧の読み取りは10秒おき
async def monitor_battery(mode):
    bat_in = analogio.AnalogIn(board.A0)
    bat_led = digitalio.DigitalInOut(board.D8)
    bat_led.direction = digitalio.Direction.OUTPUT

    # 2.0Vで1回点滅、1.9Vで2回点滅とする
    # PPKIIでの設定した際の実測を元にした
    bat_low = 1.95
    bat_verylow = 1.8

    interval = 1
    led_value = False

    bat_voltage = bat_in.value * 3.3 / 65536
    read_time = time.monotonic()
    
    while True:
        cur_time = time.monotonic()
        if cur_time - read_time >= 10.0:
            bat_voltage = bat_in.value * 3.3 / 65536
            # print(bat_voltage)
            read_time = cur_time

        if bat_voltage > bat_low:
            bat_led.value = True
            interval = 10
        elif bat_verylow <= bat_voltage < bat_low:
            # 点滅
            led_value = not led_value
            bat_led.value = led_value
            interval = 0.5
        elif bat_voltage < bat_verylow:
            # 2回点滅
            bat_led.value = True
            await asyncio.sleep(0.2)
            bat_led.value = False
            await asyncio.sleep(0.2)
            bat_led.value = True
            await asyncio.sleep(0.2)
            bat_led.value = False
            interval = 0.4

        await asyncio.sleep(interval)

async def main():
    # 省電力
    neopx_pwr = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
    neopx_pwr.direction = digitalio.Direction.OUTPUT
    neopx_pwr.value = False

    # 各プロセスを起動
    mode = Mode()

    monitor_task = asyncio.create_task(monitor_mode_pin(mode))
    led_task = asyncio.create_task(control_led(mode))
    battery_task = asyncio.create_task(monitor_battery(mode))
    await asyncio.gather(monitor_task, led_task, battery_task)

asyncio.run(main())