def fix_command(text, words=['Привет']):
    import numpy as np
    array = np.array(words)

    from pyxdameraulevenshtein import normalized_damerau_levenshtein_distance_seqs
    result = list(zip(words, list(normalized_damerau_levenshtein_distance_seqs(text, array))))

    command, rate = min(result, key=lambda x: x[1])

    # Подобранное значение для определения совпадения текста среди значений указанного списка
    # Если True, считаем что слишком много ошибок в слове, т.е. text среди all_commands нет
    if rate > 0.40:
        return

    return command


if __name__ == '__main__':
    print(fix_command('Skuqpro', ['Скайпро', 'Skypro']))  # Привет
    print(fix_command('Скуйпро', ['Скайпро']))  # Привет
    print(fix_command('Скйпро', ['Скайпро']))  # Привет
    print(fix_command('Скэйпо', ['Скайпро']))  # Привет
