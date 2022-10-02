# from pynput.keyboard import Key, Controller
from pynput import keyboard

class Addon():
    name = 'Send Keys'
    icon = None
    unit = None

    def startControl(self, topic, data):
        if type(data) == str:
            self.__presskeys(data)
        else:
            for keys in data:
                self.__presskeys(keys)

    def __presskeys(self, keys):
        contr = keyboard.Controller()
        hotkeys = keyboard.HotKey.parse(keys)
        for hotkey in hotkeys:
            contr.press(hotkey)
        hotkeys.reverse()
        for hotkey in hotkeys:
            contr.release(hotkey)


if __name__ == '__main__':
    myaddon = Addon()
    # myaddon.startControl('send-keys', ['<alt>+<F4>', '<alt>+<ctrl>+<delete>', '<ctrl>+C'])
    # myaddon.startControl('send-keys', ['<shift>+C', 'c'])
