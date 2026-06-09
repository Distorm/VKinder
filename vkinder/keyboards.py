from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def main_keyboard() -> str:
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("Следующий", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("В избранное", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("Избранное", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("В чёрный список", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("Помощь", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()
