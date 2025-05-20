import json
import os
import random
from collections import defaultdict

class AIHelper:
    """
    Класс ИИ для игры Сапер.
    Использует комбинацию опыта, логики и вероятностного анализа для принятия решений.
    """
    def __init__(self):
        self.field = None  # Текущее состояние игрового поля
        self.rows = 0      # Количество строк в поле
        self.cols = 0      # Количество столбцов в поле
        # Словарь для хранения опыта: ключ - паттерн поля, значение - список успешных ходов с их статистикой
        self.experience = defaultdict(lambda: defaultdict(int))  # pattern -> {(x,y) -> success_count}
        # Счетчики для статистики
        self.success_count = 0  # Количество успешных ходов
        self.failure_count = 0  # Количество неуспешных ходов
        # Загружаем сохраненный опыт при создании
        self.load_experience()

    def save_experience(self):
        """
        Сохраняет опыт в файл.
        Опыт включает в себя паттерны поля и успешные ходы с их статистикой.
        """
        data = {
            'experience': {},
            'success_count': self.success_count,
            'failure_count': self.failure_count
        }
        
        # Преобразуем паттерны и ходы в формат, который можно сохранить в JSON
        for pattern, moves in self.experience.items():
            if not moves:  # Пропускаем пустые паттерны
                continue
                
            pattern_str = str(pattern)  # Преобразуем кортеж в строку
            data['experience'][pattern_str] = {}
            
            for (dx, dy), count in moves.items():
                if count > 0:  # Сохраняем только ненулевые счетчики
                    move_str = f"({dx},{dy})"  # Сохраняем смещения в формате (dx,dy)
                    data['experience'][pattern_str][move_str] = count

        try:
            file_path = 'ai_experience.json'
            
            # Сначала читаем существующий файл, если он есть
            existing_data = {'experience': {}, 'success_count': 0, 'failure_count': 0}
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except:
                pass
            
            # Объединяем существующие данные с новыми
            for pattern, moves in data['experience'].items():
                if pattern not in existing_data['experience']:
                    existing_data['experience'][pattern] = {}
                for move, count in moves.items():
                    existing_data['experience'][pattern][move] = count
            
            # Сохраняем объединенные данные
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при сохранении опыта: {e}")

    def load_experience(self):
        """
        Загружает опыт из файла.
        Восстанавливает сохраненные паттерны и статистику ходов.
        """
        try:
            if os.path.exists('ai_experience.json'):
                with open('ai_experience.json', 'r') as f:
                    data = json.load(f)
                    self.experience = defaultdict(lambda: defaultdict(int))
                    for pattern_str, moves in data['experience'].items():
                        # Преобразуем строку обратно в кортеж
                        pattern = eval(pattern_str)
                        for move_str, count in moves.items():
                            # Преобразуем строку (dx,dy) обратно в кортеж
                            dx, dy = map(int, move_str.strip('()').split(','))
                            self.experience[pattern][(dx, dy)] = count
                    self.success_count = data['success_count']
                    self.failure_count = data['failure_count']
        except Exception as e:
            print(f"Ошибка при загрузке опыта: {e}")

    def set_field(self, field, rows, cols):
        """
        Устанавливает текущее состояние поля.
        Вызывается перед каждым ходом ИИ.
        """
        self.field = field
        self.rows = rows
        self.cols = cols

    def get_neighbors(self, x, y):
        """
        Получает список соседних клеток для заданной позиции.
        Включает все 8 соседних клеток (по диагонали и по сторонам).
        """
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.rows and 0 <= ny < self.cols and (dx != 0 or dy != 0):
                    neighbors.append((nx, ny))
        return neighbors

    def get_unrevealed_neighbors(self, x, y):
        """
        Получает список неоткрытых соседних клеток.
        Исключает клетки с флажками.
        """
        return [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                if not self.field[nx][ny].is_revealed and not self.field[nx][ny].is_flagged]

    def get_flagged_neighbors(self, x, y):
        """
        Получает список соседних клеток с флажками.
        Используется для подсчета известных мин вокруг клетки.
        """
        return [(nx, ny) for nx, ny in self.get_neighbors(x, y) 
                if self.field[nx][ny].is_flagged]

    def get_field_pattern(self, x, y):
        """
        Получает паттерн поля вокруг клетки (x, y).
        Паттерн - это последовательность состояний соседних клеток:
        - 'M' для мин
        - числа для открытых клеток
        - 'F' для флажков
        - 'U' для неоткрытых клеток
        """
        pattern = []
        # Получаем соседей в фиксированном порядке
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:  # Пропускаем саму клетку
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.rows and 0 <= ny < self.cols:
                        neighbors.append((nx, ny, dx, dy))  # Сохраняем и координаты, и смещения

        # Сортируем соседей для получения фиксированного порядка
        neighbors.sort(key=lambda n: (n[0], n[1]))
        
        for nx, ny, dx, dy in neighbors:
            cell = self.field[nx][ny]
            if cell.is_revealed:
                if cell.is_mine:
                    pattern.append('M')
                else:
                    pattern.append(str(cell.adjacent_mines))
            elif cell.is_flagged:
                pattern.append('F')
            else:
                pattern.append('U')
        
        return tuple(pattern), neighbors

    def learn_from_move(self, x, y, was_successful):
        """
        Запоминает результат хода.
        Если ход был успешным, увеличивает счетчик успешных ходов для данного паттерна.
        В любом случае обновляет общую статистику.
        """
        pattern, neighbors = self.get_field_pattern(x, y)
        
        if was_successful:
            # Вычисляем смещение относительно центральной клетки
            # Центральная клетка - это та, для которой мы получили паттерн
            dx = 0  # Смещение по x
            dy = 0  # Смещение по y
            
            # Ищем клетку, которая является целью хода
            for nx, ny, ndx, ndy in neighbors:
                if nx == x and ny == y:
                    dx = ndx
                    dy = ndy
                    break
            
            # Сохраняем опыт
            self.experience[pattern][(dx, dy)] += 1
            self.success_count += 1
            self.save_experience()
        else:
            self.failure_count += 1
            self.save_experience()

    def get_safe_move(self):
        """
        Находит ход, используя следующую стратегию:
        1. Проверяет опыт - если находит похожую ситуацию, делает ход с наибольшим количеством успехов
        2. Ищет безопасные ходы на основе чисел
        3. Ищет клетки с минимальным риском
        4. Если ничего не находит, выбирает случайную неоткрытую клетку
        """
        # Шаг 1: Проверяем опыт
        for x in range(self.rows):
            for y in range(self.cols):
                if not self.field[x][y].is_revealed and not self.field[x][y].is_flagged:
                    pattern, neighbors = self.get_field_pattern(x, y)
                    if pattern in self.experience:
                        # Находим ход с наибольшим количеством успехов
                        moves = self.experience[pattern]
                        if moves:
                            # Фильтруем только неоткрытые клетки
                            valid_moves = {}
                            for (dx, dy), count in moves.items():
                                nx, ny = x + dx, y + dy
                                if (0 <= nx < self.rows and 0 <= ny < self.cols and 
                                    not self.field[nx][ny].is_revealed and 
                                    not self.field[nx][ny].is_flagged):
                                    valid_moves[(nx, ny)] = count
                            
                            if valid_moves:
                                best_move = max(valid_moves.items(), key=lambda x: x[1])[0]
                                return best_move

        # Шаг 2: Ищем клетки с числами
        number_cells = []
        for x in range(self.rows):
            for y in range(self.cols):
                cell = self.field[x][y]
                if cell.is_revealed and not cell.is_mine and cell.adjacent_mines > 0:
                    number_cells.append((x, y, cell.adjacent_mines))

        # Если нет клеток с числами, ищем любую неоткрытую клетку
        if not number_cells:
            unrevealed_cells = []
            for x in range(self.rows):
                for y in range(self.cols):
                    if not self.field[x][y].is_revealed and not self.field[x][y].is_flagged:
                        unrevealed_cells.append((x, y))
            if unrevealed_cells:
                # Выбираем случайную неоткрытую клетку
                return random.choice(unrevealed_cells)

        # Шаг 3: Анализируем каждую клетку с числом
        for x, y, number in number_cells:
            unrevealed = self.get_unrevealed_neighbors(x, y)
            flagged = self.get_flagged_neighbors(x, y)
            
            # Если число равно количеству флажков, остальные клетки безопасны
            if number == len(flagged) and unrevealed:
                return unrevealed[0]

        # Шаг 4: Ищем клетку с минимальным риском
        min_risk = float('inf')
        best_moves = []

        for x in range(self.rows):
            for y in range(self.cols):
                cell = self.field[x][y]
                if cell.is_revealed or cell.is_flagged:
                    continue

                # Считаем риск для клетки
                risk = 0
                count = 0
                for nx, ny in self.get_neighbors(x, y):
                    neighbor = self.field[nx][ny]
                    if neighbor.is_revealed and not neighbor.is_mine:
                        unrevealed = self.get_unrevealed_neighbors(nx, ny)
                        flagged = self.get_flagged_neighbors(nx, ny)
                        if unrevealed:
                            remaining_mines = neighbor.adjacent_mines - len(flagged)
                            if remaining_mines > 0:
                                # Риск = оставшиеся мины / количество неоткрытых клеток
                                risk += remaining_mines / len(unrevealed)
                                count += 1

                if count > 0:
                    risk = risk / count  # Усредняем риск по всем соседним числам
                    if risk < min_risk:
                        min_risk = risk
                        best_moves = [(x, y)]
                    elif risk == min_risk:
                        best_moves.append((x, y))

        if best_moves:
            # Выбираем случайную клетку из списка клеток с минимальным риском
            return random.choice(best_moves)

        # Шаг 5: Если не нашли клетку с минимальным риском, ищем любую неоткрытую клетку
        unrevealed_cells = []
        for x in range(self.rows):
            for y in range(self.cols):
                if not self.field[x][y].is_revealed and not self.field[x][y].is_flagged:
                    unrevealed_cells.append((x, y))
        
        if unrevealed_cells:
            # Выбираем случайную неоткрытую клетку
            return random.choice(unrevealed_cells)

        return (0, 0)

    def get_mine_move(self):
        """
        Находит клетку, где точно есть мина.
        Использует логику: если число минус количество флажков равно количеству неоткрытых клеток,
        то все неоткрытые клетки содержат мины.
        """
        for x in range(self.rows):
            for y in range(self.cols):
                cell = self.field[x][y]
                if not cell.is_revealed or cell.is_mine:
                    continue

                unrevealed = self.get_unrevealed_neighbors(x, y)
                flagged = self.get_flagged_neighbors(x, y)

                # Если число минус флажки равно количеству неоткрытых, все неоткрытые - мины
                if cell.adjacent_mines - len(flagged) == len(unrevealed) and unrevealed:
                    return unrevealed[0]

        return None

    def get_stats(self):
        """
        Возвращает статистику обучения ИИ:
        - Количество успешных ходов
        - Количество неуспешных ходов
        - Процент успешных ходов
        """
        total = self.success_count + self.failure_count
        if total == 0:
            return "Нет данных"
        success_rate = (self.success_count / total) * 100
        return f"Успешных ходов: {self.success_count}, Неуспешных: {self.failure_count}, Успешность: {success_rate:.1f}%" 