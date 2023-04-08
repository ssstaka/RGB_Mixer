# HSLからRGBに変換する関数
# ここを参照した: https://www.peko-step.com/tool/hslrgb.html
# H: 0-360、S: 0-100、L: 0-100
def hsl_to_rgb(h, s, l):
    _max = None
    _min = None
    if l <= 49:
        _max = 2.55 * (l + l * (s / 100))
        _min = 2.55 * (l - l * (s / 100))
    else:
        _max = 2.55 * (l + (100 - l) * (s / 100))
        _min = 2.55 * (l - (100 - l) * (s / 100))

    # Hの範囲によって計算が変わる
    r = None
    g = None
    b = None

    if 0 <= h < 60:
        r = _max
        g = (h / 60) * (_max - _min) + _min
        b = _min
    elif 60 <= h < 120:
        r = ((120 - h) / 60) * (_max - _min) + _min
        g = _max
        b = _min
    elif 120 <= h < 180:
        r = _min
        g = _max
        b = ((h - 120) / 60) * (_max - _min) + _min
    elif 180 <= h < 240:
        r = _min
        g = ((240 - h) / 60) * (_max - _min) + _min
        b = _max
    elif 240 <= h < 300:
        r = ((h - 240) / 60) * (_max - _min) + _min
        g = _min
        b = _max
    elif 300 <= h < 360:
        r = _max
        g = _min
        b = ((360 - h) / 60) * (_max - _min) + _min
    else:
        print("error")
    
    return (round(r), round(g), round(b))